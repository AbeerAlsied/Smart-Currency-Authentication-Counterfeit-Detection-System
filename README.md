# SudanCheck AI Demo 🇸🇩

نموذج Streamlit تعليمي لتجربة فكرة تصنيف خصائص الحماية، مع بيانات تدريب مصطنعة.

## تشغيل المشروع
```bash
pip install -r requirements.txt
streamlit run app.py
```

## ما الذي أضيف؟
- نموذج Random Forest من scikit-learn.
- بيانات تدريب اصطناعية تُولّد عند تشغيل التطبيق.
- تقسيم تدريب/اختبار ومقياس دقة.
- إدخال خصائص حماية يدوياً وتجربة التصنيف.
- إمكانية تنزيل البيانات التجريبية CSV.
- واجهة رفع صورة وحفظ SHA-256 وسجل SQLite.

## تحذير علمي أساسي
البيانات مولّدة اصطناعياً وليست صوراً أو عينات عملات حقيقية. النموذج لا يتعلم خصائص التزوير الفعلية ولا يفحص صورة العملة. نتيجة النموذج مجرد تجربة برمجية لإثبات دورة تدريب/اختبار/تنبؤ، ولا يجوز استخدامها للحكم على أصالة عملة.

## الخطوة البحثية التالية
جمع مجموعة صور مصرح بها وموثقة، من إصدارات وفئات محددة، ومراجعتها مع مختصين. بعدها نبني نموذج Computer Vision ونقيّمه على مجموعة اختبار مستقلة. لا تُنشأ عينات مزيفة بغرض تداولها؛ تُستخدم بيانات بحثية آمنة ومصرح بها.

## مصادر مرجعية أولية
- Central Bank of Sudan: https://cbos.gov.sd/en/valid-currencies
- Central Bank of Sudan – 5 Sudanese Pounds: https://cbos.gov.sd/en/valid-currencies/5-sudanese-pounds
- Central Bank of Sudan – 20 Sudanese Pounds: https://cbos.gov.sd/en/valid-currencies/20-sudanese-pounds
- Neelain University repository (prior research): https://repository.neelain.edu.sd/items/28938bc9-8f74-484b-a489-f071bb330a2c

تحققي من صلاحية كل فئة وإصدار من المصدر الرسمي قبل تضمينها في النسخة البحثية.
