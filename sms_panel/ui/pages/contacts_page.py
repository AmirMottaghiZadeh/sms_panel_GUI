from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sms_panel.config import PROJECT_ROOT
from sms_panel.services.contacts import load_contacts_cache, mask_mobile, read_contacts_from_file
from sms_panel.ui.widgets import CardFrame, PrimaryButton, SecondaryButton, SelectComboBox


class ContactsPage(QWidget):
    contacts_changed = pyqtSignal(list)

    def __init__(
        self,
        contacts: list[dict[str, str]],
        *,
        default_category: str = "عمومی",
        mask_mobile_numbers: bool = False,
    ) -> None:
        super().__init__()
        self.contacts = [dict(item) for item in contacts]
        self.filtered_contacts: list[dict[str, str]] = [dict(item) for item in contacts]
        self.default_category = default_category.strip() or "عمومی"
        self.mask_mobile_numbers = bool(mask_mobile_numbers)

        root = QVBoxLayout(self)
        title = QLabel("لیست مخاطبین")
        title.setProperty("class", "fa-header")
        root.addWidget(title)

        helper = QLabel("نمایش و انتخاب مخاطبین به صورت ساختار تیک دار: دسته بندی -> نام ها")
        helper.setProperty("class", "fa-note")
        root.addWidget(helper)

        action_bar = CardFrame()
        action_layout = QVBoxLayout(action_bar)

        add_row = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("نام مخاطب")
        self.mobile_input = QLineEdit()
        self.mobile_input.setPlaceholderText("شماره موبایل")
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("دسته بندی")

        add_button = PrimaryButton("افزودن مخاطب")
        add_button.clicked.connect(self._add_contact)
        add_row.addWidget(self.name_input)
        add_row.addWidget(self.mobile_input)
        add_row.addWidget(self.category_input)
        add_row.addWidget(add_button)
        action_layout.addLayout(add_row)

        format_hint = QLabel(
            "ساختار صحیح فایل Excel/CSV: ستون ها باید دقیقا و به ترتیب name,phone,category باشند."
        )
        format_hint.setWordWrap(True)
        format_hint.setProperty("class", "fa-note")
        action_layout.addWidget(format_hint)

        tools_row = QHBoxLayout()
        import_button = SecondaryButton("ورود CSV/Excel")
        import_button.clicked.connect(self._import_contacts)
        load_cache_button = SecondaryButton("بارگذاری فایل ذخیره شده")
        load_cache_button.clicked.connect(self._load_cached_contacts)
        delete_button = SecondaryButton("حذف موارد تیک خورده")
        delete_button.clicked.connect(self._delete_checked)

        tools_row.addWidget(import_button)
        tools_row.addWidget(load_cache_button)
        tools_row.addWidget(delete_button)
        action_layout.addLayout(tools_row)

        selection_row = QHBoxLayout()
        self.category_combo = SelectComboBox()
        select_category_btn = SecondaryButton("انتخاب دسته")
        select_category_btn.clicked.connect(self._select_category)
        unselect_category_btn = SecondaryButton("لغو انتخاب دسته")
        unselect_category_btn.clicked.connect(self._unselect_category)
        select_all_btn = SecondaryButton("انتخاب همه")
        select_all_btn.clicked.connect(lambda: self._set_all_categories_state(Qt.CheckState.Checked))
        clear_btn = SecondaryButton("پاکسازی تیک ها")
        clear_btn.clicked.connect(lambda: self._set_all_categories_state(Qt.CheckState.Unchecked))

        selection_row.addWidget(QLabel("انتخاب دسته بندی"))
        selection_row.addWidget(self.category_combo)
        selection_row.addWidget(select_category_btn)
        selection_row.addWidget(unselect_category_btn)
        selection_row.addWidget(select_all_btn)
        selection_row.addWidget(clear_btn)
        action_layout.addLayout(selection_row)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو بر اساس نام/شماره/دسته")
        self.search_confirm_radio = QRadioButton("تایید جستجو")
        search_button = SecondaryButton("اجرای جستجو")
        search_button.clicked.connect(self._run_search)
        reset_button = SecondaryButton("نمایش همه")
        reset_button.clicked.connect(self._reset_search)

        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.search_confirm_radio)
        search_row.addWidget(search_button)
        search_row.addWidget(reset_button)
        action_layout.addLayout(search_row)

        root.addWidget(action_bar)

        tree_frame = CardFrame()
        tree_layout = QVBoxLayout(tree_frame)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["انتخاب/دسته بندی", "نام", "شماره"])
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        tree_layout.addWidget(self.tree)
        root.addWidget(tree_frame, 1)

        self._populate_tree(self.filtered_contacts)

    @staticmethod
    def _group_contacts(contacts: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
        grouped: dict[str, list[dict[str, str]]] = {}
        for item in contacts:
            category = str(item.get("category", "عمومی")).strip() or "عمومی"
            grouped.setdefault(category, []).append(item)

        for category in grouped:
            grouped[category] = sorted(
                grouped[category],
                key=lambda row: (
                    str(row.get("name", "")).strip().lower(),
                    str(row.get("mobile", "")).strip().lower(),
                ),
            )

        return dict(sorted(grouped.items(), key=lambda pair: pair[0].strip().lower()))

    def _populate_tree(self, contacts: list[dict[str, str]]) -> None:
        self.tree.clear()
        grouped = self._group_contacts(contacts)

        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItems(list(grouped.keys()))
        self.category_combo.blockSignals(False)

        for category, entries in grouped.items():
            parent = QTreeWidgetItem([category, "", ""])
            parent.setFlags(parent.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
            parent.setCheckState(0, Qt.CheckState.Unchecked)

            for item in entries:
                raw_mobile = str(item.get("mobile", ""))
                child = QTreeWidgetItem([
                    "",
                    str(item.get("name", "")),
                    mask_mobile(raw_mobile) if self.mask_mobile_numbers else raw_mobile,
                ])
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child.setCheckState(0, Qt.CheckState.Unchecked)
                child.setData(2, Qt.ItemDataRole.UserRole, raw_mobile)
                parent.addChild(child)

            self.tree.addTopLevelItem(parent)

        self.tree.expandAll()
        self.tree.resizeColumnToContents(0)
        self.tree.resizeColumnToContents(2)

    def _set_all_categories_state(self, state: Qt.CheckState) -> None:
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            item.setCheckState(0, state)

    def _select_category(self) -> None:
        target = self.category_combo.currentText().strip()
        if not target:
            return
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            if item.text(0).strip() == target:
                item.setCheckState(0, Qt.CheckState.Checked)
                return

    def _unselect_category(self) -> None:
        target = self.category_combo.currentText().strip()
        if not target:
            return
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            if item.text(0).strip() == target:
                item.setCheckState(0, Qt.CheckState.Unchecked)
                return

    def _add_contact(self) -> None:
        name = self.name_input.text().strip() or "بدون نام"
        mobile = self.mobile_input.text().strip()
        if not mobile:
            QMessageBox.warning(self, "مخاطبین", "شماره موبایل الزامی است.")
            return

        category = self.category_input.text().strip() or self.default_category
        self.contacts.append({"name": name, "mobile": mobile, "category": category})
        self.name_input.clear()
        self.mobile_input.clear()
        self.category_input.clear()
        self.search_input.clear()
        self._emit_changes()

    def _import_contacts(self) -> None:
        filters = "Contact Files (*.csv *.xlsx *.xls)"
        file_name, _ = QFileDialog.getOpenFileName(self, "انتخاب فایل مخاطبین", str(PROJECT_ROOT), filters)
        if not file_name:
            return

        try:
            imported = read_contacts_from_file(file_name)
        except Exception as exc:
            QMessageBox.warning(self, "مخاطبین", str(exc))
            return

        self.contacts.extend(imported)
        self.search_input.clear()
        self._emit_changes()
        QMessageBox.information(self, "مخاطبین", f"{len(imported)} مخاطب اضافه شد.")

    def _load_cached_contacts(self) -> None:
        cached = load_contacts_cache()
        if not cached:
            QMessageBox.information(self, "مخاطبین", "فایل ذخیره شده ای پیدا نشد یا خالی است.")
            return

        self.contacts.extend(cached)
        self.search_input.clear()
        self._emit_changes()
        QMessageBox.information(self, "مخاطبین", f"{len(cached)} مخاطب از فایل ذخیره شده بارگذاری شد.")

    def _delete_checked(self) -> None:
        targets: set[tuple[str, str, str]] = set()
        categories_to_delete: set[str] = set()

        for index in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(index)
            category = parent.text(0).strip() or "عمومی"

            if parent.checkState(0) == Qt.CheckState.Checked:
                categories_to_delete.add(category)
                continue

            for child_index in range(parent.childCount()):
                child = parent.child(child_index)
                if child.checkState(0) == Qt.CheckState.Checked:
                    raw_mobile = str(child.data(2, Qt.ItemDataRole.UserRole) or child.text(2)).strip()
                    targets.add((child.text(1).strip(), raw_mobile, category))

        if not categories_to_delete and not targets:
            QMessageBox.information(self, "مخاطبین", "حداقل یک دسته یا مخاطب را تیک بزنید.")
            return

        if categories_to_delete:
            self.contacts = [
                item
                for item in self.contacts
                if (str(item.get("category", "عمومی")).strip() or "عمومی") not in categories_to_delete
            ]

        if targets:
            self.contacts = [
                item
                for item in self.contacts
                if (
                    str(item.get("name", "")).strip(),
                    str(item.get("mobile", "")).strip(),
                    str(item.get("category", "عمومی")).strip() or "عمومی",
                )
                not in targets
            ]

        self._emit_changes()

    def _run_search(self) -> None:
        if not self.search_confirm_radio.isChecked():
            QMessageBox.information(self, "جستجو", "برای انجام جستجو ابتدا گزینه تایید جستجو را فعال کنید.")
            return
        self._filter_contacts(self.search_input.text())

    def _reset_search(self) -> None:
        self.search_input.clear()
        self.search_confirm_radio.setChecked(False)
        self.filtered_contacts = [dict(item) for item in self.contacts]
        self._populate_tree(self.filtered_contacts)

    def _filter_contacts(self, text: str) -> None:
        query = text.strip().lower()
        if not query:
            self.filtered_contacts = [dict(item) for item in self.contacts]
            self._populate_tree(self.filtered_contacts)
            return

        self.filtered_contacts = [
            item
            for item in self.contacts
            if (
                query in str(item.get("name", "")).lower()
                or query in str(item.get("mobile", "")).lower()
                or query in str(item.get("category", "")).lower()
            )
        ]
        self._populate_tree(self.filtered_contacts)

    def _emit_changes(self) -> None:
        if self.search_confirm_radio.isChecked() and self.search_input.text().strip():
            self._filter_contacts(self.search_input.text())
        else:
            self.filtered_contacts = [dict(item) for item in self.contacts]
            self._populate_tree(self.filtered_contacts)
        self.contacts_changed.emit([dict(item) for item in self.contacts])

    def set_contacts(self, contacts: list[dict[str, str]]) -> None:
        self.contacts = [dict(item) for item in contacts]
        if self.search_confirm_radio.isChecked() and self.search_input.text().strip():
            self._filter_contacts(self.search_input.text())
        else:
            self.filtered_contacts = [dict(item) for item in self.contacts]
            self._populate_tree(self.filtered_contacts)

    def set_default_category(self, category: str) -> None:
        value = category.strip()
        if value:
            self.default_category = value

    def set_mask_mobile_numbers(self, enabled: bool) -> None:
        self.mask_mobile_numbers = bool(enabled)
        self._populate_tree(self.filtered_contacts)
