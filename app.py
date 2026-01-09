import streamlit as st
from google import genai
from datetime import datetime
import pandas as pd
import os
import time
import pytz # დროის სარტყელისთვის
from streamlit_mic_recorder import speech_to_text

# ================== კონფიგურაცია ==================
# შენი ახალი API გასაღები
API_KEY = "AIzaSyAkxNajc8Z1XcoFlYGYg3SzcyMor5l6AOw" 
client = genai.Client(api_key=API_KEY)

USERS = {
    "Giorgi": "1234",
    "Baiko": "1234",
    "Ani": "1234",
    "admin": "0000"
}

st.set_page_config(
    page_title="Gemini 3 Smart Diary",
    layout="centered"
)

# ================== სესია ==================
if "user" not in st.session_state:
    st.session_state.user = None

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# ================== ავტორიზაცია ==================
if st.session_state.user is None:
    st.title("🔐 შესვლა")

    u = st.text_input("მომხმარებელი")
    p = st.text_input("პაროლი", type="password")

    if st.button("შესვლა", use_container_width=True):
        if u in USERS and USERS[u] == p:
            st.session_state.user = u
            st.rerun()
        else:
            st.error("❌ არასწორი მონაცემები")

    st.stop()

current_user = st.session_state.user
st.title(f"📔 {current_user}-ს ჭკვიანი დღიური")

# ================== მონაცემთა ბაზა ==================
DB_FILE = f"diary_{current_user}.csv"
COLUMNS = ["თარიღი", "საათი", "ჩანაწერი", "განწყობა", "AI_პასუხი"]

if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(DB_FILE, sep="\t", index=False)

# ================== ინტერფეისი ==================
st.subheader("🎤 ხმოვანი ჩანაწერი (დაგროვებითი)")

# --- ხმოვანი ჩაწერა ---
speech = speech_to_text(
    language="ka",
    start_prompt="🎤 დაიწყე საუბარი",
    stop_prompt="🛑 დასრულება",
    key="recorder"
)

# --- დაგროვებითი ჩაწერა ---
if speech:
    if st.session_state.input_text:
        st.session_state.input_text += " " + speech
    else:
        st.session_state.input_text = speech

# --- ტექსტური რედაქტორი ---
text = st.text_area(
    "დღიური",
    value=st.session_state.input_text,
    height=180
)

st.session_state.input_text = text

# ================== შენახვა ==================
if st.button("💾 შენახვა", use_container_width=True):

    content = st.session_state.input_text.strip()

    if not content:
        st.warning("⚠️ ტექსტი ცარიელია")
        st.stop()

    with st.spinner("🤖 Gemini 3 ამუშავებს ტექსტს..."):
        try:
            prompt = f"""
მომხმარებლის ტექსტი:
"{content}"

დავალება:
1. გაასწორე ტექსტი ქართულად (პუნქტუაცია, წინადადებები)
2. განსაზღვრე განწყობა (მაგ: ბედნიერი, სტრესული, ნეიტრალური)
3. თუ ტექსტში კითხვაა — უპასუხე დეტალურად
4. პასუხი დააბრუნე ზუსტად ამ ფორმატით:

FIXED: ...
MOOD: ...
REPLY: ...
"""

            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )

            res = response.text.strip()

            try:
                fixed = res.split("FIXED:")[1].split("MOOD:")[0].strip()
                mood = res.split("MOOD:")[1].split("REPLY:")[0].strip()
                reply = res.split("REPLY:")[1].strip()
            except Exception:
                fixed = content
                mood = "ნეიტრალური"
                reply = res

            # --- დროის გასწორება თბილისზე ---
            tbilisi_tz = pytz.timezone('Asia/Tbilisi')
            now = datetime.now(tbilisi_tz)
            
            df = pd.read_csv(DB_FILE, sep="\t")

            new_row = pd.DataFrame([[
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M"),
                fixed,
                mood,
                reply
            ]], columns=COLUMNS)

            pd.concat([df, new_row], ignore_index=True).to_csv(
                DB_FILE, sep="\t", index=False
            )

            st.session_state.input_text = ""
            st.success("✅ ჩანაწერი შენახულია")
            time.sleep(1)
            st.rerun()

        except Exception as e:
            st.error(f"❌ შეცდომა: {e}")

# ================== ისტორია ==================
st.divider()
st.subheader("📚 ისტორია")

try:
    history = pd.read_csv(DB_FILE, sep="\t")

    if history.empty:
        st.info("ჯერ ჩანაწერები არ არის")
    else:
        # ისტორიის გამოჩენა კლებადობით (ბოლო ჩანაწერი თავში)
        for _, row in history.sort_values(
            by=["თარიღი", "საათი"], ascending=False
        ).iterrows():
            with st.expander(f"🗓 {row['თარიღი']} | {row['საათი']} | {row['განწყობა']}"):
                st.write(f"✍️ {row['ჩანაწერი']}")
                st.info(f"🤖 {row['AI_პასუხი']}")
except Exception:
    st.warning("ისტორიის ჩატვირთვა ვერ მოხერხდა")
