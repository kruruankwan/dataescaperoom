import streamlit as st
import pandas as pd
import requests
import time
from pathlib import Path
import base64
import streamlit.components.v1 as components

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="DATA Escape Room",
    page_icon="🔐",
    layout="centered"
)

# =================================================
# LOAD CSS
# =================================================
with open("style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# =================================================
# CONFIG
# =================================================
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwGUE2ANKAkwQcu9ltUpy5MXhPtBtZyY6OXHdruocyvq2yvol1nkqZd6dPYD3kezkjZ/exec"

ASSETS = Path("assets")
SFX_SUCCESS = ASSETS / "sfx_door_open.mp3"     # เสียงผ่านด่าน
SFX_FAIL = ASSETS / "sfx_error_adadad.mp3"     # เสียงตอบผิด

# =================================================
# SOUND SYSTEM
# =================================================
def play_sound(path: Path):
    if not path.exists():
        return
    b64 = base64.b64encode(path.read_bytes()).decode()
    components.html(
        f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64}">
        </audio>
        """,
        height=0
    )

def queue_sound(path: Path):
    st.session_state.sound_queue = path

def flush_sound():
    if st.session_state.sound_queue:
        play_sound(st.session_state.sound_queue)
        st.session_state.sound_queue = None

# =================================================
# HELPERS
# =================================================
def reset_answer(stage):
    st.session_state.pop(f"answer_{stage}", None)

def unlock_badge(stage):
    st.session_state.badges.add(stage)

def format_time(sec):
    return f"{sec//60} นาที {sec%60} วินาที"

def log_to_sheet(group, room, stage, answer, result, time_used=""):
    payload = {
        "group_name": group,
        "classroom": room,
        "stage": stage,
        "answer": answer,
        "result": result,
        "time_used": time_used
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except:
        pass

def auto_next(stage, delay=1.2):
    time.sleep(delay)
    reset_answer(stage)
    st.session_state.stage = stage
    st.experimental_rerun()

# =================================================
# SESSION STATE INIT
# =================================================
defaults = {
    "stage": 0,
    "group_name": "",
    "room": "",
    "start_time": None,
    "completed_time": "",
    "completed_seconds": 0,
    "badges": set(),
    "hints_used": set(),
    "sound_queue": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

flush_sound()

# =================================================
# SIDEBAR
# =================================================
with st.sidebar:
    if (ASSETS / "logo_square.png").exists():
        st.image(str(ASSETS / "logo_square.png"), use_container_width=True)

    st.markdown("### 🧑‍🤝‍🧑 ทีมผู้เล่น")
    st.write("กลุ่ม:", st.session_state.group_name or "-")
    st.write("ห้อง:", st.session_state.room or "-")

    if 1 <= st.session_state.stage <= 5:
        st.progress((st.session_state.stage-1)/5)

    st.markdown("### 🏆 เหรียญ")
    cols = st.columns(5)
    for i in range(1, 6):
        with cols[i-1]:
            p = ASSETS / f"badge{i}.png"
            if i in st.session_state.badges and p.exists():
                st.image(str(p), use_container_width=True)
            else:
                st.caption(str(i))

# =================================================
# HEADER
# =================================================
if (ASSETS / "logo.png").exists():
    st.image(str(ASSETS / "logo.png"), use_container_width=True)

st.markdown(
    '<p style="text-align:center;">เกมฝึกวิเคราะห์ข้อมูล CSV สำหรับนักเรียน ม.3</p>',
    unsafe_allow_html=True
)

# =================================================
# PAGE 0 : START
# =================================================
if st.session_state.stage == 0:
    st.markdown("""
    <div class="game-card">
        <h3>🎮 กติกาเกม</h3>
        <ul>
            <li>ทั้งหมด 5 ด่าน</li>
            <li>ตอบถูก → ได้เหรียญ → ไปด่านถัดไปอัตโนมัติ</li>
            <li>กด Enter เพื่อส่งคำตอบ</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.session_state.group_name = st.text_input("ชื่อกลุ่ม")
    st.session_state.room = st.text_input("ห้องเรียน")

    if st.button("เริ่มเกม ▶"):
        if st.session_state.group_name and st.session_state.room:
            st.session_state.stage = 1
            st.session_state.start_time = time.time()
            st.experimental_rerun()
        else:
            st.warning("กรุณากรอกข้อมูลให้ครบ")

# =================================================
# STAGES 1–4 (รูปแบบเดียวกัน)
# =================================================
STAGES = {
    1: ("🔎 ด่านที่ 1 : ยอดขาย", "1_sales_50.csv", "Sales", "max", "stage1.png"),
    2: ("💪 ด่านที่ 2 : ออกกำลัง", "2_exercise_50.csv", "ExerciseMinutes", "min", "stage2.png"),
    3: ("⚡ ด่านที่ 3 : ไฟฟ้า", "3_electricity_50.csv", "Units", "max", "stage3.png"),
    4: ("🌐 ด่านที่ 4 : เว็บ", "4_web_traffic_50.csv", "Visitors", "min", "stage4.png"),
}

if st.session_state.stage in STAGES:
    title, csv, col, mode, img = STAGES[st.session_state.stage]
    st.markdown(f"<h2>{title}</h2>", unsafe_allow_html=True)
    st.image(str(ASSETS / img), use_container_width=True)

    df = pd.read_csv(csv)
    correct = getattr(df[col], mode)()

    with st.form(f"form_{st.session_state.stage}"):
        user = st.number_input("กรอกคำตอบ", key=f"answer_{st.session_state.stage}")
        ok = st.form_submit_button("ตรวจคำตอบ")

    if ok:
        result = "ถูกต้อง" if user == correct else "ผิด"
        log_to_sheet(st.session_state.group_name, st.session_state.room,
                     st.session_state.stage, user, result)

        if result == "ถูกต้อง":
            unlock_badge(st.session_state.stage)
            queue_sound(SFX_SUCCESS)
            st.balloons()
            auto_next(st.session_state.stage + 1)
        else:
            queue_sound(SFX_FAIL)
            st.error("❌ คำตอบผิด")

# =================================================
# STAGE 5
# =================================================
elif st.session_state.stage == 5:
    st.markdown("<h2>📶 ด่านที่ 5 : Wi-Fi</h2>", unsafe_allow_html=True)
    st.image(str(ASSETS / "stage5.png"), use_container_width=True)

    df = pd.read_csv("5_internet_survey_50.csv")
    correct = round(df["HoursUsed"].mean(), 2)

    with st.form("form_5"):
        user = st.number_input("คำตอบ (ทศนิยม 2 ตำแหน่ง)", format="%.2f")
        ok = st.form_submit_button("ตรวจคำตอบ")

    if ok:
        sec = int(time.time() - st.session_state.start_time)
        result = "ถูกต้อง" if user == correct else "ผิด"
        log_to_sheet(st.session_state.group_name, st.session_state.room, 5, user, result, format_time(sec))

        if result == "ถูกต้อง":
            unlock_badge(5)
            st.session_state.completed_time = format_time(sec)
            queue_sound(SFX_SUCCESS)
            st.balloons()
            auto_next(6)
        else:
            queue_sound(SFX_FAIL)
            st.error("❌ คำตอบผิด")

# =================================================
# SUMMARY
# =================================================
elif st.session_state.stage == 6:
    st.markdown("<h2>🏁 สรุปผล</h2>", unsafe_allow_html=True)
    st.write("กลุ่ม:", st.session_state.group_name)
    st.write("ห้อง:", st.session_state.room)
    st.write("เวลา:", st.session_state.completed_time)

    cols = st.columns(5)
    for i in range(1, 6):
        with cols[i-1]:
            p = ASSETS / f"badge{i}.png"
            if p.exists():
                st.image(str(p), use_container_width=True)

    if st.button("🔄 เล่นใหม่"):
        st.session_state.clear()
        st.experimental_rerun()
