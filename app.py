import streamlit as st
import pandas as pd
import requests
import time
from pathlib import Path
import base64
import streamlit.components.v1 as components

st.set_page_config(
    page_title="DATA Escape Room",
    page_icon="🔐",
    layout="centered"
)

# -------------------------------------------------
# LOAD CSS
# -------------------------------------------------
with open("style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwGUE2ANKAkwQcu9ltUpy5MXhPtBtZyY6OXHdruocyvq2yvol1nkqZd6dPYD3kezkjZ/exec"

ASSETS = Path("assets")
SFX_SUCCESS = str(ASSETS / "sfx_success.mp3")
SFX_FAIL = str(ASSETS / "sfx_fail.mp3")


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def format_time(sec: int) -> str:
    m = sec // 60
    s = sec % 60
    return f"{m} นาที {s} วินาที"


def play_sound_autoplay(path_str: str):
    """
    เล่นเสียงแบบ autoplay โดยไม่แสดงแถบ player
    path_str รับเป็น string ได้เลย เช่น "assets/sfx_success.mp3"
    """
    path = Path(path_str)
    if not path.exists():
        st.warning(f"ไม่พบไฟล์เสียง: {path_str}")
        return

    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    html = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    components.html(html, height=0)


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


def log_to_sheet(group, room, stage, answer, result, time_used=""):
    payload = {
        "group_name": group,
        "classroom": room,
        "stage": int(stage),
        "answer": answer,
        "result": result,
        "time_used": time_used
    }
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code != 200:
            st.error(f"บันทึกลงชีตไม่สำเร็จ (HTTP {r.status_code}) : {r.text[:200]}")
            return False
        return True
    except Exception as e:
        st.error(f"บันทึกลงชีตไม่สำเร็จ: {e}")
        return False


def reset_answer(stage: int):
    st.session_state.pop(f"answer_{stage}", None)


def unlock_badge(stage: int):
    st.session_state.badges.add(stage)


def stage_card(title: str, mission_html: str, image_file: str):
    st.markdown(f"""
    <div class="game-card">
        <h2>{title}</h2>
        <p>{mission_html}</p>
    </div>
    """, unsafe_allow_html=True)

    img_path = ASSETS / image_file
    if img_path.exists():
        st.image(str(img_path), use_container_width=True)
    else:
        st.warning(f"ไม่พบรูป: assets/{image_file}")


def auto_next_stage(next_stage: int, delay_sec: float = 1.2):
    """
    ไปด่านถัดไปอัตโนมัติหลังหน่วงเวลา
    (ให้เสียงเริ่มเล่น + ให้ balloons แสดงก่อน)
    """
    time.sleep(delay_sec)
    reset_answer(next_stage)
    st.session_state.stage = next_stage
    st.rerun()


HINTS = {
    1: "ใบ้: ดูคอลัมน์ <b>Sales</b> แล้วหา “ค่ามากที่สุด” (max).",
    2: "ใบ้: ดูคอลัมน์ <b>ExerciseMinutes</b> แล้วหา “ค่าน้อยที่สุด” (min).",
    3: "ใบ้: ดูคอลัมน์ <b>Units</b> แล้วหา “ค่ามากที่สุด” (max).",
    4: "ใบ้: ดูคอลัมน์ <b>Visitors</b> แล้วหา “ค่าน้อยที่สุด” (min).",
    5: "ใบ้: ดูคอลัมน์ <b>HoursUsed</b> แล้วหา “ค่าเฉลี่ย” และปัดทศนิยม 2 ตำแหน่ง (mean + round).",
}


def hint_block(stage: int):
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("💡 ขอใบ้", key=f"hint_btn_{stage}"):
            st.session_state.hints_used.add(stage)
    with c2:
        if stage in st.session_state.hints_used:
            st.info(HINTS.get(stage, ""))


def summary_page():
    st.markdown("""
    <div class="game-card">
        <h2>🏁 สรุปผลการเล่น (Mission Complete)</h2>
        <p>สุดยอด! ผ่านครบทั้ง 5 ด่านแล้ว 🎉</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🧑‍🤝‍🧑 ข้อมูลทีม")
    st.write(f"**ชื่อกลุ่ม:** {st.session_state.group_name}")
    st.write(f"**ห้อง:** {st.session_state.room}")
    st.write(f"**เวลาที่ใช้:** {st.session_state.completed_time}")

    st.markdown("### 🏆 เหรียญรางวัลที่ได้รับ")
    cols = st.columns(5)
    for i in range(1, 6):
        with cols[i - 1]:
            badge_path = ASSETS / f"badge{i}.png"
            if i in st.session_state.badges and badge_path.exists():
                st.image(str(badge_path), use_container_width=True)
            else:
                st.caption(f"ด่าน {i}")

    st.markdown("---")

    if st.button("🔄 เล่นใหม่อีกครั้ง"):
        st.session_state.stage = 0
        st.session_state.start_time = None
        st.session_state.game_completed = False
        st.session_state.completed_time = ""
        st.session_state.completed_seconds = 0
        st.session_state.badges = set()
        st.session_state.hints_used = set()
        for i in range(1, 6):
            reset_answer(i)
        st.rerun()


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
if "completed_time" not in st.session_state:
    st.session_state.completed_time = ""
if "completed_seconds" not in st.session_state:
    st.session_state.completed_seconds = 0
if "badges" not in st.session_state:
    st.session_state.badges = set()
if "hints_used" not in st.session_state:
    st.session_state.hints_used = set()


# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
with st.sidebar:
    logo_sq = ASSETS / "logo_square.png"
    if logo_sq.exists():
        st.image(str(logo_sq), use_container_width=True)

    st.markdown("## 🧑‍🤝‍🧑 ทีมผู้เล่น")
    st.write(f"**กลุ่ม:** {st.session_state.group_name or '-'}")
    st.write(f"**ห้อง:** {st.session_state.room or '-'}")

    if st.session_state.stage >= 1 and st.session_state.stage <= 5:
        st.progress(
            (st.session_state.stage - 1) / 5,
            text=f"ความคืบหน้า {st.session_state.stage-1}/5 ด่าน"
        )

    st.markdown("## 🏆 เหรียญที่ได้รับ")
    cols = st.columns(5)
    for i in range(1, 6):
        with cols[i - 1]:
            badge_path = ASSETS / f"badge{i}.png"
            if i in st.session_state.badges and badge_path.exists():
                st.image(str(badge_path), use_container_width=True)
            else:
                st.caption(str(i))

    mascot = ASSETS / "mascot.png"
    if mascot.exists():
        st.image(str(mascot), use_container_width=True)


# -------------------------------------------------
# HEADER
# -------------------------------------------------
logo = ASSETS / "logo.png"
if logo.exists():
    st.image(str(logo), use_container_width=True)

st.markdown(
    '<p style="text-align:center; opacity:0.9;">เกมฝึกวิเคราะห์ข้อมูล CSV สำหรับนักเรียน ม.3</p>',
    unsafe_allow_html=True
)


# -------------------------------------------------
# PAGE 0 — INPUT INFO
# -------------------------------------------------
if st.session_state.stage == 0:
    st.markdown("""
    <div class="game-card">
        <h3>🎮 กติกาเกม</h3>
        <ul>
            <li>มีทั้งหมด 5 ด่าน</li>
            <li>แต่ละด่านใช้ไฟล์ CSV จริง</li>
            <li>ตอบถูก → ได้เหรียญ → ไปด่านถัดไปอัตโนมัติ</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🧩 กรุณากรอกข้อมูลก่อนเริ่มเกม")
    st.session_state.group_name = st.text_input("ชื่อกลุ่ม", value=st.session_state.group_name)
    st.session_state.room = st.text_input("ห้องเรียน เช่น ม.3/1", value=st.session_state.room)

    if st.button("เริ่มเกม →"):
        if st.session_state.group_name.strip() == "" or st.session_state.room.strip() == "":
            st.warning("กรุณากรอกชื่อกลุ่มและห้องเรียนก่อน!")
        else:
            st.session_state.start_time = time.time()
            st.session_state.stage = 1
            st.session_state.game_completed = False
            st.session_state.completed_time = ""
            st.session_state.completed_seconds = 0
            st.session_state.badges = set()
            st.session_state.hints_used = set()
            for i in range(1, 6):
                reset_answer(i)
            st.rerun()


# -------------------------------------------------
# STAGE 1
# -------------------------------------------------
elif st.session_state.stage == 1:
    stage_card(
        "🔎 ด่านที่ 1 : ปลดล็อกยอดขาย",
        "<b>ภารกิจ:</b> เปิดไฟล์ CSV แล้วหาค่า <b>Sales</b> ที่มากที่สุด",
        "stage1.png"
    )
    hint_block(1)

    df = pd.read_csv("1_sales_50.csv")
    with st.expander("📁 ดาวน์โหลดไฟล์ CSV ของด่านนี้"):
        download_csv_button("1_sales_50.csv", "📥 ดาวน์โหลดไฟล์ด่านที่ 1")

    correct = df["Sales"].max()
    user = st.number_input("กรอกคำตอบ", step=1, key="answer_1")

    if st.button("ตรวจคำตอบ", key="check_1"):
        result = "ถูกต้อง" if user == correct else "ผิด"
        log_to_sheet(st.session_state.group_name, st.session_state.room, 1, user, result)

        if result == "ถูกต้อง":
            unlock_badge(1)
            play_sound_autoplay(SFX_SUCCESS)
            st.success("🎉 ถูกต้อง! กำลังไปด่านถัดไป…")
            st.balloons()
            auto_next_stage(2, delay_sec=1.2)
        else:
            play_sound_autoplay(SFX_FAIL)
            st.error("❌ คำตอบผิด ลองใหม่อีกครั้ง")


# -------------------------------------------------
# STAGE 2
# -------------------------------------------------
elif st.session_state.stage == 2:
    stage_card(
        "💪 ด่านที่ 2 : ภารกิจออกกำลัง",
        "<b>ภารกิจ:</b> เปิดไฟล์ CSV แล้วหาค่า <b>ExerciseMinutes</b> ที่น้อยที่สุด",
        "stage2.png"
    )
    hint_block(2)

    df = pd.read_csv("2_exercise_50.csv")
    with st.expander("📁 ดาวน์โหลดไฟล์ CSV ของด่านนี้"):
        download_csv_button("2_exercise_50.csv", "📥 ดาวน์โหลดไฟล์ด่านที่ 2")

    correct = df["ExerciseMinutes"].min()
    user = st.number_input("กรอกคำตอบ", step=1, key="answer_2")

    if st.button("ตรวจคำตอบ", key="check_2"):
        result = "ถูกต้อง" if user == correct else "ผิด"
        log_to_sheet(st.session_state.group_name, st.session_state.room, 2, user, result)

        if result == "ถูกต้อง":
            unlock_badge(2)
            play_sound_autoplay(SFX_SUCCESS)
            st.success("🎉 ถูกต้อง! กำลังไปด่านถัดไป…")
            st.balloons()
            auto_next_stage(3, delay_sec=1.2)
        else:
            play_sound_autoplay(SFX_FAIL)
            st.error("❌ คำตอบผิด ลองใหม่อีกครั้ง")


# -------------------------------------------------
# STAGE 3
# -------------------------------------------------
elif st.session_state.stage == 3:
    stage_card(
        "⚡ ด่านที่ 3 : ภารกิจไฟฟ้า",
        "<b>ภารกิจ:</b> เปิดไฟล์ CSV แล้วหาค่า <b>Units</b> ที่มากที่สุด",
        "stage3.png"
    )
    hint_block(3)

    df = pd.read_csv("3_electricity_50.csv")
    with st.expander("📁 ดาวน์โหลดไฟล์ CSV ของด่านนี้"):
        download_csv_button("3_electricity_50.csv", "📥 ดาวน์โหลดไฟล์ด่านที่ 3")

    correct = df["Units"].max()
    user = st.number_input("กรอกคำตอบ", step=1, key="answer_3")

    if st.button("ตรวจคำตอบ", key="check_3"):
        result = "ถูกต้อง" if abs(user - correct) < 0.01 else "ผิด"
        log_to_sheet(st.session_state.group_name, st.session_state.room, 3, user, result)

        if result == "ถูกต้อง":
            unlock_badge(3)
            play_sound_autoplay(SFX_SUCCESS)
            st.success("🎉 ถูกต้อง! กำลังไปด่านถัดไป…")
            st.balloons()
            auto_next_stage(4, delay_sec=1.2)
        else:
            play_sound_autoplay(SFX_FAIL)
            st.error("❌ คำตอบผิด ลองใหม่อีกครั้ง")


# -------------------------------------------------
# STAGE 4
# -------------------------------------------------
elif st.session_state.stage == 4:
    stage_card(
        "🌐 ด่านที่ 4 : ภารกิจเว็บทราฟฟิก",
        "<b>ภารกิจ:</b> เปิดไฟล์ CSV แล้วหาค่า <b>Visitors</b> ที่น้อยที่สุด",
        "stage4.png"
    )
    hint_block(4)

    df = pd.read_csv("4_web_traffic_50.csv")
    with st.expander("📁 ดาวน์โหลดไฟล์ CSV ของด่านนี้"):
        download_csv_button("4_web_traffic_50.csv", "📥 ดาวน์โหลดไฟล์ด่านที่ 4")

    correct = df["Visitors"].min()
    user = st.number_input("กรอกจำนวนคน", step=1, key="answer_4")

    if st.button("ตรวจคำตอบ", key="check_4"):
        result = "ถูกต้อง" if user == correct else "ผิด"
        log_to_sheet(st.session_state.group_name, st.session_state.room, 4, user, result)

        if result == "ถูกต้อง":
            unlock_badge(4)
            play_sound_autoplay(SFX_SUCCESS)
            st.success("🎉 ถูกต้อง! กำลังไปด่านถัดไป…")
            st.balloons()
            auto_next_stage(5, delay_sec=1.2)
        else:
            play_sound_autoplay(SFX_FAIL)
            st.error("❌ คำตอบผิด ลองใหม่อีกครั้ง")


# -------------------------------------------------
# STAGE 5
# -------------------------------------------------
elif st.session_state.stage == 5:
    stage_card(
        "📶 ด่านที่ 5 : ภารกิจ Wi-Fi",
        "<b>ภารกิจ:</b> หา <b>ค่าเฉลี่ย HoursUsed</b> และปัดทศนิยม 2 ตำแหน่ง",
        "stage5.png"
    )
    hint_block(5)

    df = pd.read_csv("5_internet_survey_50.csv")
    with st.expander("📁 ดาวน์โหลดไฟล์ CSV ของด่านนี้"):
        download_csv_button("5_internet_survey_50.csv", "📥 ดาวน์โหลดไฟล์ด่านที่ 5")

    correct = round(df["HoursUsed"].mean(), 2)
    user = st.number_input("กรอกคำตอบ เช่น 3.89", format="%.2f", key="answer_5")

    if st.button("ตรวจคำตอบ", key="check_5"):
        finish = time.time()
        total_sec = int(finish - st.session_state.start_time)
        formatted = format_time(total_sec)

        result = "ถูกต้อง" if float(user) == correct else "ผิด"

        ok = log_to_sheet(
            st.session_state.group_name,
            st.session_state.room,
            5,
            float(user),
            result,
            formatted
        )

        if result == "ถูกต้อง":
            unlock_badge(5)
            play_sound_autoplay(SFX_SUCCESS)
            st.success("🎉 ถูกต้อง! ผ่านครบทุกด่านแล้ว 🎉 กำลังไปหน้าสรุป…")
            st.balloons()

            # บันทึกเวลาจบเกม
            st.session_state.completed_seconds = total_sec
            st.session_state.completed_time = formatted
            st.session_state.game_completed = True

            # ไปหน้า Summary (Stage 6)
            auto_next_stage(6, delay_sec=1.3)

        else:
            play_sound_autoplay(SFX_FAIL)
            st.error("❌ คำตอบผิด ลองใหม่อีกครั้ง")


# -------------------------------------------------
# SUMMARY PAGE (STAGE 6)
# -------------------------------------------------
elif st.session_state.stage == 6:
    summary_page()
