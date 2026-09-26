# جزوه‌ی جامع فارسی دوازدهم — رضا سلیمانی

جزوه‌ی درس‌به‌درس فارسی ۳ (پایه‌ی دوازدهم): معنی، آرایه، دستور، مفهوم و قرابت، تاریخ ادبیات و بانک سؤال با پاسخ‌نامه.
بالای همه‌ی صفحه‌ها هدر «رضا سلیمانی» چاپ می‌شود.

## ساختار

| مسیر | کاربرد |
|---|---|
| `input/` | جزوه‌ها و بانک سؤال خام (منبع محتوا) |
| `jozve/lessons/` | محتوای جزوه؛ هر فایل یک بخش است و به ترتیب نام کنار هم قرار می‌گیرد |
| `jozve/css/style.css` | طراحی و رنگ‌بندی |
| `jozve/build.cjs` | ساخت PDF (هدر، شماره‌صفحه، فهرست خودکار) |
| `output/jozve-farsi12.pdf` | خروجی نهایی |

## ساخت PDF

```bash
pip install pymupdf
NODE_PATH=$(npm root -g) node jozve/build.cjs            # فقط PDF
NODE_PATH=$(npm root -g) node jozve/build.cjs --preview  # PDF + تصویر صفحه‌ها در output/preview
```

نیازمند Node.js با Playwright و Chromium، و پایتون با pymupdf.
فونت‌ها: وزیرمتن (Vazirmatn)، Noto Naskh Arabic و Noto Nastaliq Urdu — همه با مجوز OFL.
