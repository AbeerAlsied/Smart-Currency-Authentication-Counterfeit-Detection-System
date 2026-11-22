import streamlit as st
from PIL import Image
import numpy as np
import sqlite3
import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from functools import lru_cache
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "sudancheck.db"
KNOWLEDGE_PATH = APP_DIR / "data" / "reference_features.json"
DEMO_DATA_PATH = APP_DIR / "data" / "synthetic_training_data.csv"

st.set_page_config(page_title="SudanCheck | فحص العملة", page_icon="🇸🇩", layout="wide")
st.markdown("""
<style>
.stApp { background: #f3f7fa; }
.block-container { padding-top: 1.5rem; }
h1, h2, h3, p, label { direction: rtl; text-align: right; }
div[data-testid="stMetric"] { background: white; padding: 14px; border-radius: 12px; }
.note { background:#fff3cd; padding:14px; border-radius:10px; direction:rtl; }
</style>
""", unsafe_allow_html=True)

FEATURES = [
    "watermark", "security_thread", "raised_print",
    "see_through_register", "microtext"
]
FEATURE_LABELS = {
    "watermark": "العلامة المائية",
    "security_thread": "خيط التأمين",
    "raised_print": "الطباعة البارزة",
    "see_through_register": "علامة التطابق بين الوجهين",
    "microtext": "الكتابة الدقيقة"
}

def make_synthetic_dataset(n=1600, seed=42):
    """بيانات مصطنعة للتجربة البرمجية فقط، وليست صور أو عينات نقدية حقيقية."""
    rng = np.random.default_rng(seed)
    X = rng.integers(0, 2, size=(n, len(FEATURES)))
    # قاعدة تعليمية اصطناعية مع بعض الضوضاء حتى لا تكون البيانات مثالية.
    score = (
        1.4 * X[:, 0] + 1.5 * X[:, 1] + 1.0 * X[:, 2]
        + 1.2 * X[:, 3] + 0.9 * X[:, 4]
    )
    probability = 1 / (1 + np.exp(-(score - 3.0)))
    y = (rng.random(n) < probability).astype(int)
    df = pd.DataFrame(X, columns=FEATURES)
    df["demo_label"] = np.where(y == 1, "مطابقة للنمط التجريبي", "تحتاج مراجعة")
    return df

@st.cache_resource
def train_demo_model():
    df = make_synthetic_dataset()
    X = df[FEATURES]
    y = (df["demo_label"] == "مطابقة للنمط التجريبي").astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    model = RandomForestClassifier(
        n_estimators=180, max_depth=7, min_samples_leaf=3, random_state=42
    )
    model.fit(X_train, y_train)
    accuracy = accuracy_score(y_test, model.predict(X_test))
    return model, accuracy, df

def db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS checks (
        id TEXT PRIMARY KEY, created_at TEXT, denomination TEXT,
        filename TEXT, image_sha256 TEXT, width INTEGER, height INTEGER,
        aspect_ratio REAL, result TEXT, notes TEXT, previous_hash TEXT,
        record_hash TEXT
    )""")
    con.commit()
    return con

def get_last_hash(con):
    row = con.execute("SELECT record_hash FROM checks ORDER BY created_at DESC LIMIT 1").fetchone()
    return row[0] if row else "GENESIS"

def add_record(denomination, filename, image_bytes, width, height, ratio, result, notes):
    con = db()
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    previous_hash = get_last_hash(con)
    record_id = str(uuid.uuid4())
    created = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    payload = "|".join([record_id, created, denomination, image_hash, str(width),
                        str(height), f"{ratio:.6f}", result, notes, previous_hash])
    record_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    con.execute("INSERT INTO checks VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (record_id, created, denomination, filename, image_hash, width,
                 height, ratio, result, notes, previous_hash, record_hash))
    con.commit()
    con.close()
    return record_id, image_hash, record_hash

def load_knowledge():
    try:
        return json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"denominations": {}}

st.title("🇸🇩 SudanCheck")
st.subheader("نموذج أولي ذكي لدعم فحص العملة السودانية")
st.markdown("""
<div class="note">
<strong>تنبيه بحثي:</strong> نموذج الذكاء الاصطناعي في هذه النسخة مدرّب على بيانات مصطنعة لأغراض تجربة الكود وواجهة التصنيف فقط.
لا يستخدم صوراً حقيقية لعملات أصلية أو مزيفة، ولا يمكن اعتبار نتيجته حكماً على أصالة أي ورقة نقدية.
</div>
""", unsafe_allow_html=True)

model, demo_accuracy, demo_df = train_demo_model()
knowledge = load_knowledge()
denoms = list(knowledge.get("denominations", {}).keys()) or [
    "500 جنيه (مرجع أولي)", "5 جنيهات (مرجع توثيقي)", "20 جنيهاً (مرجع توثيقي)"
]

tab1, tab2, tab3, tab4 = st.tabs([
    "فحص صورة", "تجربة نموذج AI", "قاعدة المعرفة", "سجل الفحوصات"
])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        denomination = st.selectbox("اختاري فئة العملة", denoms)
        uploaded = st.file_uploader("ارفعي صورة العملة", type=["jpg", "jpeg", "png"])
        st.caption("رفع الصورة هنا لحفظها كبصمة رقمية وعرض معلوماتها؛ لا يجري النموذج تدريباً أو حكماً بصرياً عليها.")
    if uploaded:
        try:
            image = Image.open(uploaded).convert("RGB")
            image_bytes = uploaded.getvalue()
            width, height = image.size
            ratio = width / height if height else 0
            with col2:
                st.image(image, caption="الصورة المرفوعة", use_container_width=True)
            a, b, c = st.columns(3)
            a.metric("العرض", f"{width}px")
            b.metric("الارتفاع", f"{height}px")
            c.metric("نسبة الأبعاد", f"{ratio:.2f}")
            st.info("للحصول على تجربة النموذج، انتقلي إلى تبويب «تجربة نموذج AI» وأدخلي ملاحظات الفحص.")
            notes = st.text_area("ملاحظات الفاحص (اختياري)")
            if st.button("حفظ سجل الصورة"):
                record_id, image_hash, record_hash = add_record(
                    denomination, uploaded.name, image_bytes, width, height, ratio,
                    "IMAGE_STORED_NOT_AUTHENTICATED", notes
                )
                st.success("تم حفظ سجل الصورة.")
                st.code(f"رقم السجل: {record_id}\nSHA-256 الصورة: {image_hash}\nHash السجل: {record_hash}")
                st.caption("هذه سلسلة Hash محلية تجريبية وليست Blockchain موزعة.")
        except Exception as e:
            st.error(f"تعذر قراءة الصورة: {e}")
    else:
        st.info("ارفعي صورة لعرض معلوماتها وحفظ سجلها.")

with tab2:
    st.markdown("### تجربة نموذج التصنيف")
    st.write("اختاري ما إذا كانت خصائص الحماية التالية ظاهرة أثناء الفحص اليدوي. النموذج يتعلم من بيانات مصطنعة فقط.")
    inputs = {}
    c1, c2 = st.columns(2)
    for i, feature in enumerate(FEATURES):
        target = c1 if i % 2 == 0 else c2
        with target:
            inputs[feature] = st.selectbox(
                FEATURE_LABELS[feature], ["غير ظاهرة / غير متحققة", "ظاهرة / متحققة"],
                key=f"ai_{feature}"
            ) == "ظاهرة / متحققة"
    if st.button("حلّل الخصائص التجريبية", type="primary"):
        sample = pd.DataFrame([[int(inputs[f]) for f in FEATURES]], columns=FEATURES)
        probability = float(model.predict_proba(sample)[0][1])
        predicted = int(model.predict(sample)[0])
        if predicted == 1:
            st.success("نتيجة النموذج: الخصائص أقرب إلى النمط الإيجابي في البيانات التجريبية.")
        else:
            st.warning("نتيجة النموذج: الخصائص تحتاج مراجعة وفق النمط التجريبي.")
        st.metric("احتمال الفئة الإيجابية داخل النموذج التجريبي", f"{probability*100:.1f}%")
        st.caption("هذه النسبة ليست احتمال أصالة العملة الحقيقية. هي مخرجات نموذج مدرّب على بيانات مولّدة اصطناعياً.")
    st.divider()
    st.markdown("### معلومات تدريب النموذج")
    m1, m2 = st.columns(2)
    m1.metric("عدد السجلات المصطنعة", f"{len(demo_df):,}")
    m2.metric("دقة الاختبار على البيانات المصطنعة", f"{demo_accuracy*100:.1f}%")
    st.warning("ارتفاع الدقة هنا لا يعني نجاح كشف التزوير في الواقع؛ لأن بيانات التدريب والاختبار مولّدة من القاعدة الاصطناعية نفسها.")
    csv = demo_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("تحميل البيانات التجريبية CSV", csv, "synthetic_training_data.csv", "text/csv")
    st.dataframe(demo_df.head(12), use_container_width=True)

with tab3:
    st.markdown("### قاعدة المعرفة الأولية")
    st.write("هذه نسخة JSON مبسطة يمكن تطويرها لاحقاً إلى RDF/OWL وSPARQL.")
    for name, details in knowledge.get("denominations", {}).items():
        with st.expander(name):
            st.write("المصدر:", details.get("source", "غير محدد"))
            for feature in details.get("features", []):
                st.write("•", feature)
    st.warning("يجب التحقق من حالة تداول كل فئة وإصدار من بنك السودان المركزي قبل اعتمادها.")

with tab4:
    con = db()
    rows = con.execute("""SELECT created_at, denomination, filename, result, image_sha256,
                          previous_hash, record_hash FROM checks ORDER BY created_at DESC LIMIT 100""").fetchall()
    con.close()
    if rows:
        st.dataframe([{
            "التاريخ":r[0], "الفئة":r[1], "اسم الملف":r[2], "الحالة":r[3],
            "SHA-256 الصورة":r[4][:16]+"…", "الهاش السابق":r[5][:16]+"…",
            "هاش السجل":r[6][:16]+"…"
        } for r in rows], use_container_width=True)
    else:
        st.info("لا توجد سجلات حتى الآن.")

st.divider()
st.caption("SudanCheck AI Demo • Prototype for academic research • لا يُعد بديلاً عن فحص الجهات المختصة")
