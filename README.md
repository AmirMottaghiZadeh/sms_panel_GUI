# پنل دسکتاپ SMS.ir (PyQt6)

اپلیکیشن دسکتاپ مدیریت پیامک برای سرویس `SMS.ir` با رابط فارسی، معماری ماژولار، و تمرکز روی استفاده روزمره مدرسه/سازمان.

## ویژگی ها

- ارسال پیام تکی و گروهی
- مدیریت مخاطبین (CSV/Excel)
- مدیریت پیش نویس ها
- نمایش گزارش ها و اعتبار پنل
- تم روشن/تیره و انتخاب رنگ رابط
- ساختار کدنویسی ماژولار برای توسعه تیمی

## پیش نیازها

- Python `3.10+`
- سیستم عامل لینوکس/ویندوز (PyQt6)

## نصب و اجرا

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m sms_panel
```

گزینه جایگزین:

```bash
python3 sms_panel_desktop.py
```

## تنظیمات اولیه

- تنظیمات اصلی در `sms_panel_settings.json` ذخیره می شود.
- برای شروع امن:
  1) فایل `sms_panel_settings.example.json` را کپی کنید با نام `sms_panel_settings.json`
  2) کلید API را یا در خود برنامه وارد کنید یا داخل `sms_api.txt` قرار دهید
- در اجرای اول اگر API Key تنظیم نشده باشد، پنجره ورود کلید نمایش داده می شود.

## نکات امنیتی (مهم برای ریپوی پابلیک)

- فایل های زیر خصوصی هستند و نباید در GitHub پابلیک شوند:
  - `sms_api.txt`
  - `sms_panel_settings.json`
  - `contacts_import_cache.json`
- این فایل ها در `.gitignore` اضافه شده اند.
- اگر قبلا کلید واقعی API را در جایی منتشر کرده اید، حتما آن را از پنل `SMS.ir` **Rotate/Revoke** کنید.

## ساختار پروژه

```text
sms_panel/
  app.py
  config.py
  core/
    models.py
    workers.py
  services/
    settings_store.py
    sms_ir_client.py
    contacts.py
    drafts.py
    response_parser.py
  ui/
    main_window.py
    theme.py
    widgets.py
    dialogs/
      api_key_dialog.py
    pages/
      dashboard_page.py
      send_page.py
      drafts_page.py
      contacts_page.py
      reports_page.py
      credit_page.py
      settings_page.py
sms_panel_desktop.py
```

## وابستگی ها

فایل `requirements.txt` شامل وابستگی های اصلی پروژه است:

- `PyQt6`
- `requests`
- `smsir-python`
- `pandas`
- `openpyxl`

## انتشار و مشارکت

- مجوز پروژه: `MIT` (فایل `LICENSE`)
- راهنمای مشارکت: `CONTRIBUTING.md`
