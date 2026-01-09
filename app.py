import streamlit as st
import google.generativeai as genai
from datetime import datetime
import pandas as pd
import os
from streamlit_mic_recorder import speech_to_text

# --- კონფიგურაცია ---
# ჩასვი შენი სულ ახალი გასაღები აქ:
API_KEY = "AIzaSyAgZjH7-PPa8zcHfU2d5oSaiHFEKbkyBG8" 

# Gemini-ს დაკავშირება უსაფრთხოების ფილტრების გარეშე (რომ არ დაიბლოკოს)
genai.configure(api_key=API_KEY)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

USERS = {"giorgi": "1234", "admin": "0000"}

st.set_page_config(page_title="AI Smart Diary 2026", layout="centered")

# --- ავტორიზაცია ---
if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"] is None:
    st.title("🔐 შესვლა")
    u = st.text_input("მომხმარებელი:")
    p = st.text_input("პაროლი:", type="password")
    if st.button("შესვლა"):
        if u in USERS and USERS[u] == p:
            st.session_state["user"] = u
            st.rerun()
    st.stop()

current_user = st.session_state["user"]
st.title(f"🚀 {current_user}-ს დღიური")

# --- მონაცემთა ბაზა ---
DB_FILE = f"diary_{current_user}.csv"
if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=["თარიღი", "საათი", "ჩანაწერი", "განწყობა", "AI_პასუხი"]).to_csv(DB_FILE, sep='\t', index=False)

# --- ინტერფეისი ---
st.subheader("🎤 ისაუბრე ან ჩაწერე")
text_from_speech = speech_to_text(language='ka', start_prompt="ჩაწერა (ისაუბრე)", key='recorder')
user_input = st.text_area("ტექსტი:", value=text_from_speech if text_from_speech else "", height=100)

if st.button("💾 შენახვა და AI დამუშავება"):
    if user_input:
        with st.spinner('Gemini ფიქრობს...'):
            try:
                # ვცდილობთ დაკავშირებას ყველაზე სტაბილურ მოდელთან
                model="gemini-3-flash-preview"
                
                prompt = f"""
                დღეს არის 2026 წლის 9 იანვარი. მომხმარებელმა დაწერა: "{user_input}"
                დავალება:
                1. გაასწორე ტექსტი: დაამატე მძიმეები და წერტილები.
                2. თუ საუბარია ამინდზე, უპასუხე როგორც მეგობარმა.
                3. პასუხი დააბრუნე ასე:
                FIXED: [ტექსტი] | MOOD: [განწყობა] | REPLY: [პასუხი]
                """
                
                response = model.generate_content(prompt, safety_settings=safety_settings)
                res = response.text
                
                fixed = res.split("FIXED:")[1].split("| MOOD:")[0].strip()
                mood = res.split("MOOD:")[1].split("| REPLY:")[0].strip()
                reply = res.split("REPLY:")[1].strip()
            except Exception as e:
                fixed, mood, reply = user_input, "შეცდომა", f"AI-მ ვერ უპასუხა: {e}"

            # შენახვა
            now = datetime.now()
            df = pd.read_csv(DB_FILE, sep='\t')
            new_row = pd.DataFrame([[now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), fixed, mood, reply]], 
                                   columns=["თარიღი", "საათი", "ჩანაწერი", "განწყობა", "AI_პასუხი"])
            pd.concat([df, new_row], ignore_index=True).to_csv(DB_FILE, sep='\t', index=False)
            st.success("შენახულია!")
            st.rerun()

# --- ისტორია ---
st.divider()
try:
    df_hist = pd.read_csv(DB_FILE, sep='\t')
    for i, row in df_hist.sort_values(by=["თარიღი", "საათი"], ascending=False).iterrows():
        with st.expander(f"🗓️ {row['თარიღი']} | {row['განწყობა']}"):
            st.write(f"✍️ **გასწორებული:** {row['ჩანაწერი']}")
            st.info(f"🤖 **AI:** {row['AI_პასუხი']}")
except:
    st.write("ჩანაწერები ჯერ არ არის.")
