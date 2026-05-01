from __future__ import annotations

from datetime import datetime
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sms_panel.services.contacts import mask_mobile
from sms_panel.ui.widgets import PrimaryButton, SecondaryButton


class SendPage(QWidget):
    send_single_requested = pyqtSignal(str, str, str)
    send_group_requested = pyqtSignal(str, list, str)
    send_contacts_requested = pyqtSignal(str, list, str)
    draft_saved = pyqtSignal(dict)
    contacts_changed = pyqtSignal(list)
    line_number_changed = pyqtSignal(str)

    def __init__(
        self,
        contacts: list[dict[str, str]],
        line_number: str,
        drafts: list[dict[str, Any]] | None = None,
        available_lines: list[str] | None = None,
        *,
        default_category: str = "عمومی",
        mask_mobile_numbers: bool = False,
    ) -> None:
        super().__init__()
        self.contacts = [dict(item) for item in contacts]
        self.drafts: list[dict[str, Any]] = [dict(item) for item in (drafts or [])]
        self.available_lines: list[str] = [item.strip() for item in (available_lines or []) if item.strip()]
        self.default_category = default_category.strip() or "عمومی"
        self.mask_mobile_numbers = bool(mask_mobile_numbers)
        self.root = QVBoxLayout(self)

        title = QLabel("ارسال پیام")
        title.setProperty("class", "fa-header")
        self.root.addWidget(title)

        self.tabs = QTabWidget()
        self.root.addWidget(self.tabs)

        self.single_tab = self._build_single_tab()
        self.group_tab = self._build_group_tab()
        self.contacts_tab = self._build_contacts_tab()
        self.tabs.addTab(self.single_tab, "ارسال تکی")
        self.tabs.addTab(self.group_tab, "ارسال گروهی")
        self.tabs.addTab(self.contacts_tab, "از لیست مخاطبین")

        self.set_drafts(self.drafts)
        self.set_available_lines(self.available_lines, line_number)
        self.refresh_contacts_tree()

    def _build_single_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form = QGroupBox("ارسال پیام تکی")
        form_layout = QVBoxLayout(form)

        self.single_line_combo = QComboBox()
        self.single_line_combo.currentTextChanged.connect(self._sync_line_selection)
        self.single_mobile = QLineEdit()
        self.single_mobile.setPlaceholderText("شماره موبایل")
        self.single_message = QPlainTextEdit()
        self.single_message.setPlaceholderText("متن پیام")
        self.single_message.setMaximumHeight(140)
        self.single_draft_combo = self._create_draft_combo(self._apply_single_draft)

        send = PrimaryButton("ارسال پیام تکی")
        send.clicked.connect(self._emit_single)

        save_draft = SecondaryButton("ذخیره پیش نویس")
        save_draft.clicked.connect(self._save_single_draft)

        form_layout.addWidget(QLabel("شماره خط ارسال"))
        form_layout.addWidget(self.single_line_combo)
        form_layout.addWidget(QLabel("شماره موبایل"))
        form_layout.addWidget(self.single_mobile)
        form_layout.addWidget(QLabel("متن پیام"))
        form_layout.addWidget(self.single_message)
        form_layout.addWidget(QLabel("انتخاب پیش نویس"))
        form_layout.addWidget(self.single_draft_combo)
        form_layout.addWidget(send)
        form_layout.addWidget(save_draft)

        layout.addWidget(form)
        layout.addStretch(1)
        return tab

    def _build_group_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form = QGroupBox("ارسال پیام گروهی")
        form_layout = QVBoxLayout(form)

        self.group_line_combo = QComboBox()
        self.group_line_combo.currentTextChanged.connect(self._sync_line_selection)
        self.group_mobiles = QPlainTextEdit()
        self.group_mobiles.setPlaceholderText("هر شماره را در یک خط وارد کنید")
        self.group_mobiles.setMaximumHeight(170)
        self.group_message = QPlainTextEdit()
        self.group_message.setPlaceholderText("متن پیام")
        self.group_message.setMaximumHeight(140)
        self.group_draft_combo = self._create_draft_combo(self._apply_group_draft)

        send = PrimaryButton("ارسال گروهی")
        send.clicked.connect(self._emit_group)
        save_draft = SecondaryButton("ذخیره پیش نویس")
        save_draft.clicked.connect(self._save_group_draft)

        form_layout.addWidget(QLabel("شماره خط ارسال"))
        form_layout.addWidget(self.group_line_combo)
        form_layout.addWidget(QLabel("شماره ها"))
        form_layout.addWidget(self.group_mobiles)
        form_layout.addWidget(QLabel("متن پیام"))
        form_layout.addWidget(self.group_message)
        form_layout.addWidget(QLabel("انتخاب پیش نویس"))
        form_layout.addWidget(self.group_draft_combo)
        form_layout.addWidget(send)
        form_layout.addWidget(save_draft)

        layout.addWidget(form)
        layout.addStretch(1)
        return tab

    def _build_contacts_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        manager = QGroupBox("مدیریت مخاطبین")
        manager_layout = QVBoxLayout(manager)

        add_row = QHBoxLayout()
        self.contact_name = QLineEdit()
        self.contact_name.setPlaceholderText("نام")
        self.contact_mobile = QLineEdit()
        self.contact_mobile.setPlaceholderText("شماره موبایل")
        self.contact_category = QLineEdit()
        self.contact_category.setPlaceholderText("دسته بندی")

        add_button = SecondaryButton("افزودن")
        add_button.clicked.connect(self._add_contact)

        add_row.addWidget(self.contact_name)
        add_row.addWidget(self.contact_mobile)
        add_row.addWidget(self.contact_category)
        add_row.addWidget(add_button)
        manager_layout.addLayout(add_row)

        controls_row = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.setPlaceholderText("انتخاب دسته")
        select_category_btn = SecondaryButton("انتخاب دسته")
        select_category_btn.clicked.connect(self._select_category)
        unselect_category_btn = SecondaryButton("لغو انتخاب دسته")
        unselect_category_btn.clicked.connect(self._unselect_category)
        select_all_btn = SecondaryButton("انتخاب همه دسته ها")
        select_all_btn.clicked.connect(lambda: self._set_all_categories_state(Qt.CheckState.Checked))
        clear_btn = SecondaryButton("پاکسازی انتخاب")
        clear_btn.clicked.connect(lambda: self._set_all_categories_state(Qt.CheckState.Unchecked))

        controls_row.addWidget(QLabel("اولویت انتخاب: دسته بندی ← نام ها"))
        controls_row.addWidget(self.category_combo)
        controls_row.addWidget(select_category_btn)
        controls_row.addWidget(unselect_category_btn)
        controls_row.addWidget(select_all_btn)
        controls_row.addWidget(clear_btn)
        manager_layout.addLayout(controls_row)

        self.contacts_tree = QTreeWidget()
        self.contacts_tree.setColumnCount(3)
        self.contacts_tree.setHeaderLabels(["دسته بندی", "نام", "شماره"])
        self.contacts_tree.setAlternatingRowColors(True)
        manager_layout.addWidget(self.contacts_tree)

        send_box = QGroupBox("ارسال از لیست مخاطبین")
        send_layout = QVBoxLayout(send_box)
        self.contacts_line_combo = QComboBox()
        self.contacts_line_combo.currentTextChanged.connect(self._sync_line_selection)
        self.contacts_message = QPlainTextEdit()
        self.contacts_message.setMaximumHeight(130)
        self.contacts_message.setPlaceholderText("متن پیام")
        self.contacts_draft_combo = self._create_draft_combo(self._apply_contacts_draft)

        send_button = PrimaryButton("ارسال به مخاطبین انتخاب شده")
        send_button.clicked.connect(self._emit_contact_send)

        send_layout.addWidget(QLabel("شماره خط ارسال"))
        send_layout.addWidget(self.contacts_line_combo)
        send_layout.addWidget(QLabel("متن پیام"))
        send_layout.addWidget(self.contacts_message)
        send_layout.addWidget(QLabel("انتخاب پیش نویس"))
        send_layout.addWidget(self.contacts_draft_combo)
        send_layout.addWidget(send_button)

        layout.addWidget(manager)
        layout.addWidget(send_box)
        return tab

    def _create_draft_combo(self, callback: Any) -> QComboBox:
        combo = QComboBox()
        combo.currentIndexChanged.connect(callback)
        return combo

    def _populate_draft_combo(self, combo: QComboBox) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("انتخاب پیش نویس")
        for item in self.drafts:
            combo.addItem(str(item.get("title", "بدون عنوان")), str(item.get("message", "")))
        combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def _apply_single_draft(self, index: int) -> None:
        self._apply_draft_to_editor(self.single_draft_combo, self.single_message, index)

    def _apply_group_draft(self, index: int) -> None:
        self._apply_draft_to_editor(self.group_draft_combo, self.group_message, index)

    def _apply_contacts_draft(self, index: int) -> None:
        self._apply_draft_to_editor(self.contacts_draft_combo, self.contacts_message, index)

    @staticmethod
    def _apply_draft_to_editor(combo: QComboBox, editor: QPlainTextEdit, index: int) -> None:
        if index <= 0:
            return
        text = combo.itemData(index)
        if isinstance(text, str):
            editor.setPlainText(text)

    def _emit_single(self) -> None:
        self.send_single_requested.emit(
            self.single_line_combo.currentText().strip(),
            self.single_mobile.text().strip(),
            self.single_message.toPlainText().strip(),
        )

    def _emit_group(self) -> None:
        numbers = [item.strip() for item in self.group_mobiles.toPlainText().splitlines() if item.strip()]
        self.send_group_requested.emit(
            self.group_line_combo.currentText().strip(),
            numbers,
            self.group_message.toPlainText().strip(),
        )

    def _emit_contact_send(self) -> None:
        selected: list[str] = []
        seen: set[str] = set()

        def add_mobile(value: str) -> None:
            mobile = value.strip()
            if mobile and mobile not in seen:
                seen.add(mobile)
                selected.append(mobile)

        for category_index in range(self.contacts_tree.topLevelItemCount()):
            category_item = self.contacts_tree.topLevelItem(category_index)
            for child_index in range(category_item.childCount()):
                child = category_item.child(child_index)
                if child.checkState(0) == Qt.CheckState.Checked:
                    raw_mobile = str(child.data(2, Qt.ItemDataRole.UserRole) or child.text(2)).strip()
                    add_mobile(raw_mobile)

        self.send_contacts_requested.emit(
            self.contacts_line_combo.currentText().strip(),
            selected,
            self.contacts_message.toPlainText().strip(),
        )

    def _prompt_draft_title(self, default_title: str) -> str:
        title, ok = QInputDialog.getText(
            self,
            "ذخیره پیش نویس",
            "عنوان پیش نویس:",
            QLineEdit.EchoMode.Normal,
            default_title,
        )
        if not ok:
            return ""
        return title.strip()

    def _save_single_draft(self) -> None:
        message = self.single_message.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "پیش نویس", "متن پیام خالی است.")
            return

        title = self._prompt_draft_title("پیش نویس ارسال تکی")
        if not title:
            return

        draft = {
            "title": title,
            "type": "single",
            "line": self.single_line_combo.currentText().strip(),
            "mobiles": [self.single_mobile.text().strip()],
            "message": message,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.draft_saved.emit(draft)

    def _save_group_draft(self) -> None:
        message = self.group_message.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "پیش نویس", "متن پیام خالی است.")
            return

        title = self._prompt_draft_title("پیش نویس ارسال گروهی")
        if not title:
            return

        draft = {
            "title": title,
            "type": "group",
            "line": self.group_line_combo.currentText().strip(),
            "mobiles": [item.strip() for item in self.group_mobiles.toPlainText().splitlines() if item.strip()],
            "message": message,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.draft_saved.emit(draft)

    def _add_contact(self) -> None:
        name = self.contact_name.text().strip()
        mobile = self.contact_mobile.text().strip()
        if not mobile:
            QMessageBox.warning(self, "مخاطبین", "شماره موبایل الزامی است.")
            return

        self.contacts.append(
            {
                "name": name or "بدون نام",
                "mobile": mobile,
                "category": self.contact_category.text().strip() or self.default_category,
            }
        )
        self.contact_name.clear()
        self.contact_mobile.clear()
        self.contact_category.clear()
        self.refresh_contacts_tree()
        self.contacts_changed.emit(self.contacts)

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

    def refresh_contacts_tree(self) -> None:
        self.contacts_tree.clear()
        grouped = self._group_contacts(self.contacts)

        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItems(list(grouped.keys()))
        self.category_combo.blockSignals(False)

        for category, entries in grouped.items():
            category_item = QTreeWidgetItem([category, "", ""])
            category_item.setFlags(category_item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
            category_item.setCheckState(0, Qt.CheckState.Unchecked)

            for contact in entries:
                raw_mobile = str(contact.get("mobile", ""))
                child = QTreeWidgetItem([
                    "",
                    str(contact.get("name", "")),
                    mask_mobile(raw_mobile) if self.mask_mobile_numbers else raw_mobile,
                ])
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child.setCheckState(0, Qt.CheckState.Unchecked)
                child.setData(2, Qt.ItemDataRole.UserRole, raw_mobile)
                category_item.addChild(child)

            self.contacts_tree.addTopLevelItem(category_item)

        self.contacts_tree.expandAll()

    def _set_all_categories_state(self, state: Qt.CheckState) -> None:
        for index in range(self.contacts_tree.topLevelItemCount()):
            item = self.contacts_tree.topLevelItem(index)
            item.setCheckState(0, state)

    def _select_category(self) -> None:
        target = self.category_combo.currentText().strip()
        if not target:
            return
        for index in range(self.contacts_tree.topLevelItemCount()):
            item = self.contacts_tree.topLevelItem(index)
            if item.text(0).strip() == target:
                item.setCheckState(0, Qt.CheckState.Checked)
                return

    def _unselect_category(self) -> None:
        target = self.category_combo.currentText().strip()
        if not target:
            return
        for index in range(self.contacts_tree.topLevelItemCount()):
            item = self.contacts_tree.topLevelItem(index)
            if item.text(0).strip() == target:
                item.setCheckState(0, Qt.CheckState.Unchecked)
                return

    def set_available_lines(self, lines: list[str], preferred_line: str = "") -> None:
        cleaned_lines = [item.strip() for item in lines if item and item.strip()]
        if not cleaned_lines and preferred_line:
            cleaned_lines = [preferred_line]
        if not cleaned_lines:
            cleaned_lines = [""]

        self.available_lines = cleaned_lines
        for combo in (self.single_line_combo, self.group_line_combo, self.contacts_line_combo):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(cleaned_lines)
            combo.blockSignals(False)

        target_line = preferred_line.strip() if preferred_line else cleaned_lines[0]
        self.set_line_number(target_line)

    def set_line_number(self, line: str) -> None:
        for combo in (self.single_line_combo, self.group_line_combo, self.contacts_line_combo):
            combo.blockSignals(True)
            index = combo.findText(line)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)

    def _sync_line_selection(self, line: str) -> None:
        line = line.strip()
        if not line:
            return

        for combo in (self.single_line_combo, self.group_line_combo, self.contacts_line_combo):
            if combo.currentText() == line:
                continue
            combo.blockSignals(True)
            index = combo.findText(line)
            if index >= 0:
                combo.setCurrentIndex(index)
            combo.blockSignals(False)
        self.line_number_changed.emit(line)

    def set_contacts(self, contacts: list[dict[str, str]]) -> None:
        self.contacts = [dict(item) for item in contacts]
        self.refresh_contacts_tree()

    def set_drafts(self, drafts: list[dict[str, Any]]) -> None:
        self.drafts = [dict(item) for item in drafts]
        self._populate_draft_combo(self.single_draft_combo)
        self._populate_draft_combo(self.group_draft_combo)
        self._populate_draft_combo(self.contacts_draft_combo)

    def set_default_category(self, category: str) -> None:
        value = category.strip()
        if value:
            self.default_category = value

    def set_mask_mobile_numbers(self, enabled: bool) -> None:
        self.mask_mobile_numbers = bool(enabled)
        self.refresh_contacts_tree()
