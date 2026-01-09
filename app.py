import streamlit as st
from google import genai
from datetime import datetime
import pandas as pd
import os
import time
from streamlit_mic_recorder import speech_to_text

# --- კონფიგურაცია ---
API_KEY = "AIzaSyAgZjH7-PPa8zcHfU2d5oSaiHFEKbkyBG8"
client = genai.Client(api_key=API_KEY)

USERS = {"Giorgi": "1234", "Baiko": "1234", "Ani": "1234", "admin": "0000"}

st.set_page_config(page_title="Gemini 3 Smart Diary", layout="centered")

# --- სესიის ინიციალიზაცია ---
if "user" not in st.session_state:
    st.session_state["user"] = None
if "temp_content" not in st.session_state:
    st.session_state["temp_content"] = ""
if "is_processing_speech" not in st.session_state:
    st.session_state["is_processing_speech"] = False

# --- ავტორიზაცია ---
if st.session_state["user"] is None:
    st.title("🔐 შესვლა")
    u = st.text_input("მომხმარებელი:", key="login_user")
    p = st.text_input("პაროლი:", type="password", key="login_pass")
    if st.button("შესვლა"):
        if u in USERS and USERS[u] == p:
            st.session_state["user"] = u
            st.rerun()
        else:
            st.error("არასწორი მონაცემები!")
    st.stop()

current_user = st.session_state["user"]
st.title(f"🚀 {current_user}-ს დღიური")

# --- მონაცემთა ბაზა ---
DB_FILE = f"diary_{current_user}.csv"
COLUMNS = ["თარიღი", "საათი", "ჩანაწერი", "განწყობა", "AI_პასუხი"]

if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(DB_FILE, sep='\t', index=False)

# --- ინტერფეისი ---
st.subheader("🎤 ისაუბრე ან ჩაწერე")

# ხმოვანი შეყვანა
t_speech = speech_to_text(
    language='ka', 
    start_prompt="🎤 დაიწყე საუბარი", 
    stop_prompt="🛑 დასრულება",
    key='recorder'
)

# ტელეფონისთვის სპეციალური დამუშავება: თუ ხმა მოვიდა, ვაჩვენებთ ლოდინს
if t_speech:
    with st.spinner("⏳ ხმა მუშავდება, გთხოვთ დაელოდოთ..."):
        st.session_state["temp_content"] = t_speech
        time.sleep(1) # მცირე პაუზა ტელეფონის ბრაუზერისთვის
        st.rerun()

# ტექსტური ველი
user_text = st.text_area(
    "რა ხდება დღეს?", 
    value=st.session_state["temp_content"],
    height=150,
    key="diary_widget",
    help="აქ გამოჩნდება თქვენი ნალაპარაკები ტექსტი"
)

# შენახვის ღილაკი
save_btn = st.button("💾 შენახვა", use_container_width=True)

if save_btn:
    raw_content = st.session_state["diary_widget"]
    
    if raw_content and raw_content.strip():
        with st.spinner('🤖 Gemini 3 აანალიზებს...'):
            try:
                prompt = f"""
                მომხმარებელმა დაწერა: "{raw_content}"
                დავალება:
                1. გაასწორე ტექსტი: დაამატე მძიმეები და წერტილები ქართულად.
                2. თუ არის კითხვა, უპასუხე დეტალურად.
                3. პასუხი დააბრუნე ფორმატით: FIXED: [ტექსტი] | MOOD: [განწყობა] | REPLY: [პასუხი]
                """
                
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt
                )
                res = response.text
                
                if "FIXED:" in res and "MOOD:" in res and "REPLY:" in res:
                    fixed = res.split("FIXED:")[1].split("| MOOD:")[0].strip()
                    mood = res.split("MOOD:")[1].split("| REPLY:")[0].strip()
                    reply = res.split("| REPLY:")[1].strip()
                else:
                    fixed, mood, reply = raw_content, "ნეიტრალური", res
                
                # შენახვა ფაილში
                now = datetime.now()
                df = pd.read_csv(DB_FILE, sep='\t')
                new_row = pd.DataFrame([[
                    now.strftime("%Y-%m-%d"), 
                    now.strftime("%H:%M"), 
                    fixed, 
                    mood, 
                    reply
                ]], columns=COLUMNS)
                
                pd.concat([df, new_row], ignore_index=True).to_csv(DB_FILE, sep='\t', index=False)
                
                # გასუფთავება
                st.session_state["temp_content"] = ""
                st.success("✅ ჩანაწერი შენახულია!")
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"❌ AI შეცდომა: {str(e)}")
    else:
        st.warning("⚠️ გთხოვთ, ჯერ შეიყვანოთ ტექსტი ან ჩაწეროთ ხმა.")

# --- ისტორია ---
st.divider()
try:
    df_hist = pd.read_csv(DB_FILE, sep='\t')
    if not df_hist.empty:
        st.write("📚 **ბოლო ჩანაწერები:**")
        for i, row in df_hist.sort_values(by=["თარიღი", "საათი"], ascending=False).iterrows():
            with st.expander(f"🗓️ {row['თარიღი']} | {row['საათი']} | {row['განწყობა']}"):
                st.write(f"✍️ {row['ჩანაწერი']}")
                st.info(f"🤖 {row['AI_პასუხი']}")
except Exception:
    st.write("📭 ჩანაწერები ჯერ არ არის.")
