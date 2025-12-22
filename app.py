


import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from pathlib import Path 

st.set_page_config(
    page_title="DATA Escape Room",
    page_icon="🔐",
    layout="centered"
)

#โหลดไฟล์ css
with open("style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.markdown('<h1 class="main-title">🔐 DATA Escape Room</h1>', unsafe_allow_html=True)
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwGUE2ANKAkwQcu9ltUpy5MXhPtBtZyY6OXHdruocyvq2yvol1nkqZd6dPYD3kezkjZ/exec"

# -------------------------------------------------
# FUNCTION : SEND LOG TO GOOGLE SHEET
# -------------------------------------------------
def log_to_sheet(group, room, stage, answer, result, time_used=""):
    payload = {
        "group_name": (group),
        "classroom": (room),
        "stage": int(stage),
        "answer": answer,          # ถ้าอยากบังคับชนิด: float(answer) / int(answer)
        "result": (result),
        "time_used": (time_used)
    }

    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        # ถ้าไม่ใช่ 200 จะขึ้นแจ้งทันที
        if r.status_code != 200:
            st.error(f"บันทึกลงชีตไม่สำเร็จ (HTTP {r.status_code}) : {r.text[:200]}")
            return False
        return True
    except Exception as e:
        st.error(f"บันทึกลงชีตไม่สำเร็จ: {e}")
        return False


def download_csv_button(path: str, label: str):
    p = Path(path)
    if p.exists():
        st.download_button(
            label=label,
            data=p.read_bytes(),
            file_name=p.name,
            mime="text/csv"
        )
    else:
        st.warning(f"ไม่พบไฟล์สำหรับดาวน์โหลด: {path}")

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "stage" not in st.session_state:
    st.session_state.stage = 0

if "group_name" not in st.session_state:
    st.session_state.group_name = ""

if "room" not in st.session_state:
    st.session_state.room = ""

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "game_completed" not in st.session_state:
    st.session_state.game_completed = False


# -------------------------------------------------
# THEME (ดำ–น้ำเงิน–ม่วง)
# -------------------------------------------------
st.markdown("""
<style>
    body {
        background-color: #0d0f1a;
        color: white;
    }
    .stButton>button {
        background-color: #6a0dad;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border: 2px solid #9b5cff;
    }
    .stTextInput>div>input {
        background-color: #1b1e2b;
        color: #fff;
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.markdown('<h1 class="sub-title">5 ด่ า น ไ ข ร หั ส ข้ อ มู ล 🔐</h1>', unsafe_allow_html=True)

# -------------------------------------------------
# SHOW TIMER
# -------------------------------------------------
if st.session_state.start_time:
    elapsed = int(time.time() - st.session_state.start_time)
    m = elapsed // 60
    s = elapsed % 60
    st.info(f"⏳ เวลาที่ผ่านไป: **{m} นาที {s} วินาที**")


# -------------------------------------------------
# PAGE 0 — INPUT INFO
# -------------------------------------------------
if st.session_state.stage == 0:
    st.markdown("### 🧩 กรุณากรอกข้อมูลก่อนเริ่มเกม")

    st.session_state.group_name = st.text_input("ชื่อกลุ่ม")
    st.session_state.room = st.text_input("ห้องเรียน เช่น ม.3/1")

    if st.button("เริ่มเกม →"):
        if st.session_state.group_name.strip() == "" or st.session_state.room.strip() == "":
            st.warning("กรุณากรอกชื่อกลุ่มและห้องเรียนก่อน!")
        else:
            st.session_state.start_time = time.time()  # เริ่มจับเวลา
            st.session_state.stage = 1
            st.session_state.game_completed = False
            st.rerun()


# -------------------------------------------------
# STAGE 1 — MAX SALES
# -------------------------------------------------
elif st.session_state.stage == 1:
    st.markdown("## 🔎 ด่านที่ 1 : หายอดขายสูงสุด")

    df = pd.read_csv("1_sales_50.csv")

    with st.expander("📁 ดาวน์โหลดไฟล์ CSV ของด่านนี้"):
        download_csv_button("1_sales_50.csv", "📥 ดาวน์โหลดไฟล์ด่านที่ 1")

    correct = df["Sales"].max()
    user = st.number_input("กรอกคำตอบ", step=1)

    if st.button("ตรวจคำตอบ"):
        result = "ถูกต้อง" if user == correct else "ผิด"
        log_to_sheet(st.session_state.group_name, st.session_state.room, 1, user, result)

        if result == "ถูกต้อง":
            st.success("🎉 ถูกต้อง! ไปด่านถัดไป →")
            st.session_state.stage = 2
            st.rerun()
        else:
            st.error("❌ คำตอบผิด")


# -------------------------------------------------
# STAGE 2 — EXERCISE Min
# -------------------------------------------------
elif st.session_state.stage == 2:
    st.markdown(
    '<h2 class="stage-title">💪 ด่านที่ 2 : คนที่ออกกำลังกายน้อยที่สุดกี่วัน</h2>',
    unsafe_allow_html=True
)

    df = pd.read_csv("2_exercise_50.csv")

    with st.expander("📁 ดาวน์โหลดไฟล์ CSV ของด่านนี้"):
        download_csv_button("2_exercise_50.csv", "📥 ดาวน์โหลดไฟล์ด่านที่ 2")

    correct = (df["ExerciseMinutes"]).min()
    user = st.number_input("กรอกจำนวนคน", step=1)

    if st.button("ตรวจคำตอบ"):
        result = "ถูกต้อง" if user == correct else "ผิด"
        log_to_sheet(st.session_state.group_name, st.session_state.room, 2, user, result)

        if result == "ถูกต้อง":
            st.success("🎉 เก่งมาก! ไปด่านที่ 3 →")
            st.session_state.stage = 3
            st.rerun()
        else:
            st.error("❌ คำตอบผิด")


# -------------------------------------------------
# STAGE 3 — AVERAGE INTERNET HOURS
# -------------------------------------------------
elif st.session_state.stage == 3:
    st.markdown("## 🌐 ด่านที่ 3 : หน่วยไฟฟ้าที่ใช้สูงสุด ")

    df = pd.read_csv("3_electricity_50.csv")

    with st.expander("📁 ดาวน์โหลดไฟล์ CSV ของด่านนี้"):
        download_csv_button("3_electricity_50.csv", "📥 ดาวน์โหลดไฟล์ด่านที่ 3")

    correct = df["Units"].max()
    user = st.number_input("กรอกคำตอบ", step=1)

    if st.button("ตรวจคำตอบ"):
        result = "ถูกต้อง" if abs(user - correct) < 0.01 else "ผิด"
        log_to_sheet(st.session_state.group_name, st.session_state.room, 3, user, result)

        if result == "ถูกต้อง":
            st.success("🎉 ดีมาก! ไปด่าน 4 →")
            st.session_state.stage = 4
            st.rerun()
        else:
            st.error("❌ คำตอบไม่ถูก")


# -------------------------------------------------
# STAGE 4 — MIN WEBSITE VISITORS (UPDATED)
# -------------------------------------------------
elif st.session_state.stage == 4:
    st.markdown(
        '<h2 class="stage-title">📊 ด่านที่ 4 : หาจำนวนคนที่เข้าเว็บน้อยที่สุด</h2>',
    unsafe_allow_html=True
)

    df = pd.read_csv("4_web_traffic_50.csv")

    with st.expander("📁 ดาวน์โหลดไฟล์ CSV ของด่านนี้"):
        download_csv_button("4_web_traffic_50.csv", "📥 ดาวน์โหลดไฟล์ด่านที่ 4")

    correct = df["Visitors"].min()
    user = st.number_input("กรอกจำนวนคน", step=1)

    if st.button("ตรวจคำตอบ"):
        result = "ถูกต้อง" if user == correct else "ผิด"
        log_to_sheet(st.session_state.group_name, st.session_state.room, 4, user, result)

        if result == "ถูกต้อง":
            st.success("🎉 ยอดเยี่ยม! ไปด่านสุดท้าย →")
            st.session_state.stage = 5
            st.rerun()
        else:
            st.error("❌ คำตอบผิด")


# -------------------------------------------------
# STAGE 5 — MAX ELECTRICITY
# -------------------------------------------------
elif st.session_state.stage == 5:
    st.markdown("## ⚡ ด่านที่ 5 : ค่าเฉลี่ยเวลาการใช้อินเทอร์เน็ต (ทศนิยม 2 ตำแหน่ง)")

    df = pd.read_csv("5_internet_survey_50.csv")

    with st.expander("📁 ดาวน์โหลดไฟล์ CSV ของด่านนี้"):
        download_csv_button("5_internet_survey_50.csv", "📥 ดาวน์โหลดไฟล์ด่านที่ 5")

    correct = round(df["HoursUsed"].mean(), 2)
    user = st.number_input("กรอกคำตอบ เช่น 3.89", format="%.2f")

    HOME_URL = "https://ev-car01.my.canva.site/dataescaperoom"

    if st.button("ตรวจคำตอบ"):
        finish = time.time()
        total_sec = int(finish - st.session_state.start_time)
        m = total_sec // 60
        s = total_sec % 60
        formatted = f"{m} นาที {s} วินาที"

        result = "ถูกต้อง" if float(user) == correct else "ผิด"

        ok = log_to_sheet(
            st.session_state.group_name,
            st.session_state.room,
            5,
            float(user),
            result,
            formatted
        )

        if result == "ถูกต้อง" and ok:
            st.success(f"🎉 ผ่านครบทุกด่าน! ใช้เวลา {formatted}")
            st.balloons()
            st.session_state.game_completed = True
        elif result == "ถูกต้อง" and not ok:
            st.warning("ตอบถูกแล้ว แต่บันทึกลง Google Sheet ไม่สำเร็จ (ดูข้อความ error ด้านบน)")
        else:
            st.error("❌ คำตอบผิด")

    if st.session_state.game_completed:
        st.markdown(
            f"""
            <div style="margin-top: 18px;">
                <a class="home-link-btn" href="{HOME_URL}" target="_blank" rel="noopener noreferrer">
                  🏠 กลับหน้าหลัก
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

