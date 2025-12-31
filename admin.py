import streamlit as st
import pandas as pd
import re
from pathlib import Path
from datetime import datetime

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Admin Dashboard — Escape Room",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# LOAD CSS
# -----------------------------
CSS_PATH = Path("style.css")
if CSS_PATH.exists():
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
else:
    st.warning("ไม่พบไฟล์ style.css (ควรอยู่โฟลเดอร์เดียวกับ admin.py)")

# -----------------------------
# HEADER
# -----------------------------
st.image("assets/logo.png", use_container_width=True)
st.markdown(
    '<p style="text-align:center; opacity:0.9;">แดชบอร์ดควบคุมครู — ผล DATA Escape Room</p>',
    unsafe_allow_html=True
)

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQIHdSOZCCAyAPLg41A9no_hJmAhm9dPV4lim7xxBctg-WSJxrnO5Uc6bdD9WSo16o0krwa6319JQ1p/pub?output=csv"

# -----------------------------
# HELPERS
# -----------------------------
@st.cache_data(ttl=60)
def load_sheet(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

def convert_time_to_seconds(t):
    """แปลง 'x นาที y วินาที' -> วินาที"""
    if pd.isna(t):
        return None
    m = re.search(r"(\d+)\s*นาที\s*(\d+)\s*วินาที", str(t))
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))

def sec_to_mmss(sec):
    if sec is None or pd.isna(sec):
        return "-"
    sec = int(sec)
    return f"{sec//60:02d}:{sec%60:02d}"

def kpi_html(title: str, value: str, sub: str = "") -> str:
    return f"""
    <div class="kpi-box">
      <div class="kpi-title">{title}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>
    """

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.image("assets/logo_square.png", use_container_width=True)
    st.markdown("## ⚙️ ตัวกรองข้อมูล")

    if st.button("🔄 รีเฟรชข้อมูลทันที"):
        st.cache_data.clear()
        st.rerun()

# -----------------------------
# LOAD DATA
# -----------------------------
try:
    df = load_sheet(SHEET_CSV_URL)
except Exception as e:
    st.error(f"โหลดข้อมูลไม่สำเร็จ: {e}")
    st.stop()

# -----------------------------
# CLEAN / NORMALIZE
# -----------------------------
# columns fallback
for col in ["group_name", "classroom", "stage", "result", "time_used", "timestamp"]:
    if col not in df.columns:
        df[col] = None

# types
df["stage"] = pd.to_numeric(df["stage"], errors="coerce")
df["time_seconds"] = df["time_used"].apply(convert_time_to_seconds)

if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

# -----------------------------
# FILTERS (sidebar)
# -----------------------------
with st.sidebar:
    # last update time (local)
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    st.caption(f"อัปเดตล่าสุด: {now_str}")

    # group filter
    groups = sorted(df["group_name"].dropna().astype(str).unique().tolist())
    group_filter = st.multiselect("เลือกกลุ่ม", groups, default=groups)
    if group_filter:
        df = df[df["group_name"].astype(str).isin(group_filter)]

    # room filter
    rooms = sorted(df["classroom"].dropna().astype(str).unique().tolist())
    room_filter = st.multiselect("เลือกห้อง", rooms, default=rooms)
    if room_filter:
        df = df[df["classroom"].astype(str).isin(room_filter)]

    # stage filter
    stages = sorted(df["stage"].dropna().astype(int).unique().tolist())
    stage_filter = st.multiselect("เลือกด่าน", stages, default=stages)
    if stage_filter:
        df = df[df["stage"].isin(stage_filter)]

# -----------------------------
# KPI SUMMARY (ต้องนิยามตัวแปรก่อนใช้งาน)
# -----------------------------
total = len(df)
correct_n = int((df["result"] == "ถูกต้อง").sum())
wrong_n = int((df["result"] == "ผิด").sum())
acc = (correct_n / total * 100) if total > 0 else 0.0

unique_groups = int(df["group_name"].dropna().nunique())
unique_rooms = int(df["classroom"].dropna().nunique())

# จบเกม = stage 5 ถูกต้อง + มีเวลา
done_df = df[(df["stage"] == 5) & (df["result"] == "ถูกต้อง")].dropna(subset=["time_seconds", "group_name"])
done_groups = int(done_df["group_name"].nunique()) if len(done_df) else 0
avg_finish = float(done_df.groupby("group_name")["time_seconds"].min().mean()) if len(done_df) else None

# -----------------------------
# KPI CARDS (แบบในภาพ)
# -----------------------------
st.markdown("## 📌 ภาพรวม")
st.markdown(
    f"""
    <div class="kpi-grid">
      {kpi_html("รายการทั้งหมด", f"{total}", "Attempts (หลังกรอง)")}
      {kpi_html("ตอบถูก", f"{correct_n}", "รวมทุกด่าน")}
      {kpi_html("ตอบผิด", f"{wrong_n}", "รวมทุกด่าน")}
      {kpi_html("ความถูกต้อง", f"{acc:.1f}%", "Correct / Total")}
      {kpi_html("จำนวนกลุ่ม", f"{unique_groups}", f"จำนวนห้อง {unique_rooms}")}
      {kpi_html("จบเกม", f"{done_groups}", f"เวลาเฉลี่ย {sec_to_mmss(avg_finish) if avg_finish else '-'}")}
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("<hr/>", unsafe_allow_html=True)

# -----------------------------
# LEADERBOARD
# -----------------------------
st.markdown("## 🏆 Leaderboard (ผ่านครบทุกด่าน) — เรียงตามเวลา")

# ----- เงื่อนไข: ผ่านครบทุกด่าน (1-5) -----
REQUIRED_STAGES = {1, 2, 3, 4, 5}

# เอาเฉพาะรายการที่ "ถูกต้อง" และ stage อยู่ใน 1-5
ok = df[(df["result"] == "ถูกต้อง") & (df["stage"].isin(list(REQUIRED_STAGES)))].copy()

# กันเคส stage เป็น float
ok["stage"] = ok["stage"].astype(int)

# กลุ่มที่ผ่านครบทุกด่าน = มี stage ครบ 1-5
passed_all = (
    ok.groupby(["group_name", "classroom"])["stage"]
      .apply(lambda s: set(s.unique()) >= REQUIRED_STAGES)
      .reset_index(name="passed_all")
)

passed_all = passed_all[passed_all["passed_all"] == True][["group_name", "classroom"]]

# ----- เวลาอันดับ: ใช้เวลาจบเกม (stage 5 ถูกต้อง) ที่เร็วสุดของกลุ่ม -----
finish = df[(df["stage"] == 5) & (df["result"] == "ถูกต้อง")].dropna(subset=["time_seconds"]).copy()

# เวลาเร็วสุดต่อกลุ่ม/ห้อง
best_time = (
    finish.groupby(["group_name", "classroom"])["time_seconds"]
          .min()
          .reset_index()
)

# รวมเงื่อนไข "ผ่านครบทุกด่าน" + "มีเวลาจบ"
leader = passed_all.merge(best_time, on=["group_name", "classroom"], how="inner")

# เรียงตามเวลา
leader = leader.sort_values("time_seconds", ascending=True).reset_index(drop=True)

if len(leader) == 0:
    st.info("ยังไม่พบผู้เล่นที่ผ่านครบทุกด่าน (1–5) และมีเวลาจบเกม (stage 5 ถูกต้อง)")
else:
    leader.insert(0, "อันดับ", leader.index + 1)
    leader["เวลา"] = leader["time_seconds"].apply(sec_to_mmss)

    # โชว์ทุกคน (ไม่จำกัด Top10)
    st.dataframe(
        leader[["อันดับ", "group_name", "classroom", "เวลา"]],
        use_container_width=True,
        hide_index=True
    )


# -----------------------------
# CHARTS
# -----------------------------
st.markdown("## 📈 สถิติการตอบถูก/ผิดรายด่าน")

if total > 0 and df["stage"].notna().any():
    chart_data = df.groupby(["stage", "result"]).size().unstack(fill_value=0).sort_index()
    st.bar_chart(chart_data)
else:
    st.info("ข้อมูลยังไม่เพียงพอสำหรับแสดงกราฟ")

st.markdown("<hr/>", unsafe_allow_html=True)

# -----------------------------
# FULL TABLE
# -----------------------------
st.markdown("## 📋 ตารางข้อมูลทั้งหมด (หลังกรอง)")

# จัดคอลัมน์ที่ควรโชว์
show_cols = ["timestamp", "group_name", "classroom", "stage", "answer", "result", "time_used", "time_seconds"]
for c in show_cols:
    if c not in df.columns:
        df[c] = None

st.dataframe(df[show_cols].sort_values(by="timestamp", ascending=False, na_position="last"),
            use_container_width=True)

# -----------------------------
# DOWNLOAD
# -----------------------------
st.markdown("## 📥 ดาวน์โหลดข้อมูล")
csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "ดาวน์โหลด CSV (หลังกรอง)",
    csv_bytes,
    file_name="escape_room_results_filtered.csv",
    mime="text/csv"
)
