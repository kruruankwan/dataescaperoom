import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Admin Dashboard — Escape Room", page_icon="📊", layout="wide")
st.title("📊 Dashboard — ผล DATA Escape Room")

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQIHdSOZCCAyAPLg41A9no_hJmAhm9dPV4lim7xxBctg-WSJxrnO5Uc6bdD9WSo16o0krwa6319JQ1p/pub?output=csv"

@st.cache_data(ttl=60)
def load_sheet(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

try:
    df = load_sheet(SHEET_CSV_URL)
except Exception as e:
    st.error(f"โหลดข้อมูลไม่สำเร็จ: {e}")
    st.stop()

# --- Clean ---
if "time_used" not in df.columns:
    df["time_used"] = None

if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

def convert_time(t):
    if pd.isna(t):
        return None
    m = re.search(r"(\d+)\s*นาที\s*(\d+)\s*วินาที", str(t))
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))

df["time_seconds"] = df["time_used"].apply(convert_time)

# --- Sidebar filter ---
st.sidebar.header("🔎 ตัวกรองข้อมูล")

if "group_name" in df.columns:
    groups = sorted(df["group_name"].dropna().unique().tolist())
    group_filter = st.sidebar.multiselect("เลือกกลุ่ม", groups, default=groups)
    df = df[df["group_name"].isin(group_filter)]

if "classroom" in df.columns:
    rooms = sorted(df["classroom"].dropna().unique().tolist())
    room_filter = st.sidebar.multiselect("เลือกห้อง", rooms, default=rooms)
    df = df[df["classroom"].isin(room_filter)]

# --- Show table ---
#st.subheader("📋 ตารางข้อมูลทั้งหมด")
#st.subheader("✅ สรุปแบบ 1 กลุ่ม = 1 แถว (เฉพาะที่ตอบถูก)")

df2 = df.copy()
df2["stage"] = pd.to_numeric(df2["stage"], errors="coerce")
if "timestamp" in df2.columns:
    df2["timestamp"] = pd.to_datetime(df2["timestamp"], errors="coerce")

done = df2[df2["result"] == "ถูกต้อง"].sort_values("timestamp")

# เลือกแถวล่าสุดของแต่ละ (กลุ่ม, ห้อง, ด่าน)
last = done.groupby(["group_name", "classroom", "stage"], as_index=False).tail(1)

# pivot คำตอบด่าน 1-5 ให้อยู่แถวเดียว
pivot = last.pivot_table(
    index=["group_name", "classroom"],
    columns="stage",
    values="answer",
    aggfunc="first"
).reset_index()

pivot = pivot.rename(columns={1: "ด่าน1", 2: "ด่าน2", 3: "ด่าน3", 4: "ด่าน4", 5: "ด่าน5"})

# ดึงเวลา (เฉพาะด่าน 5)
t5 = last[last["stage"] == 5][["group_name", "classroom", "time_used"]].drop_duplicates(
    subset=["group_name", "classroom"], keep="last"
)

summary = pivot.merge(t5, on=["group_name", "classroom"], how="left")

st.subheader("✅ สรุปแบบ 1 กลุ่ม = 1 แถว (เฉพาะที่ตอบถูก)")
st.dataframe(summary)

# st.dataframe(df)  # <-- คอมเมนต์/ลบทิ้ง เพื่อไม่ให้ตาราง log แสดง


# --- Summary ---
st.subheader("📊 สรุป")
col1, col2 = st.columns(2)

with col1:
    if "group_name" in df.columns:
        st.metric("จำนวนกลุ่ม", df["group_name"].nunique())
    st.metric("จำนวนรายการทั้งหมด", len(df))

with col2:
    if "result" in df.columns:
        st.metric("ตอบถูกทั้งหมด", (df["result"] == "ถูกต้อง").sum())
        st.metric("ตอบผิดทั้งหมด", (df["result"] == "ผิด").sum())

# --- Ranking: เฉพาะจบเกม (stage 5 ถูกต้อง) ---
if all(c in df.columns for c in ["stage", "result", "group_name", "time_seconds"]):
    done = df[(df["stage"] == 5) & (df["result"] == "ถูกต้อง")].dropna(subset=["time_seconds", "group_name"])
    if len(done) > 0:
        st.subheader("🏆 อันดับเวลาเร็วสุด (เฉพาะกลุ่มที่จบเกม)")
        rank = done.groupby("group_name")["time_seconds"].min().sort_values()
        st.table(rank.reset_index().rename(columns={"time_seconds": "เวลา (วินาที)"}))

# --- Charts ---
if all(c in df.columns for c in ["stage", "result"]):
    st.subheader("📈 กราฟคำตอบถูก/ผิด")
    chart_data = df.groupby(["stage", "result"]).size().unstack(fill_value=0)
    st.bar_chart(chart_data)

# --- Download ---
st.subheader("📥 ดาวน์โหลดข้อมูล")
csv = df.to_csv(index=False).encode("utf-8-sig")
st.download_button("ดาวน์โหลด CSV", csv, "escape_room_results.csv", "text/csv")



