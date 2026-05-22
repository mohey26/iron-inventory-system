# 🏗️ نظام إدارة مخزون الحديد (Iron Inventory System)

نظام ويب بسيط ومجاني لإدارة مخزون الحديد في المستودعات والمتاجر، يعمل **بالكامل على الهاتف دون اتصال بالإنترنت**، مناسب جداً للمبتدئين.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.0+-lightgrey?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-green?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📱 مميزات النظام

- ✅ إدارة المنتجات: إضافة وتعديل منتجات الحديد (زاوية، مربع، دائري...)
- 📥 تسجيل الوارد: المشتريات من الموردين مع السعر والتاريخ
- 📤 تسجيل الصادر: المبيعات أو الاستهلاك في التصنيع
- ⚠️ تنبيهات ذكية عند نقص المخزون تحت الحد الأدنى
- 📊 تقارير يومية وشهرية مع إمكانية تصدير CSV
- 📷 دعم مسح الباركود (قريباً)
- 📱 واجهة متجاوبة تماماً مع الهواتف (تصميم جوال أولاً)
- 🌐 **يعمل دون إنترنت** - كل شيء محلي على هاتفك
- 🇸🇦 دعم كامل للغة العربية

---

## 🧰 التقنيات المستخدمة

| التقنية | الاستخدام |
|---------|-----------|
| Python + Flask | الخادم الخفيف |
| SQLite | قاعدة بيانات بدون إعدادات |
| Bootstrap 5 (RTL) | واجهة عربية جميلة وسريعة |
| Vanilla JavaScript | تفاعل الصفحات |

---

## 🚀 تشغيل النظام على هاتفك (Termux)

### 1. تثبيت Termux
- حمّل تطبيق [Termux](https://termux.com/) من متجر F-Droid (أحدث نسخة)

### 2. تحميل المشروع
افتح Termux وانسخ الأوامر التالية بالترتيب:

```bash
# تحديث الحزم الأساسية
pkg update -y && pkg upgrade -y

# تثبيت Git و Python
pkg install git python -y

# نسخ المستودع (المشروع)
git clone https://github.com/mohey26/iron-inventory-system.git

# الدخول إلى مجلد المشروع
cd iron-inventory-system
