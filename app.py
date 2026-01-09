import streamlit as st
from google import genai
from datetime import datetime
import pandas as pd
import os
from streamlit_mic_recorder import speech_to_text

# --- კონფიგურაცია ---
API_KEY = "AIzaSyAgZjH7-PPa8zcHfU2d5oSaiHFEKbkyBG8"
client = genai.Client(api_key=API_KEY)

USERS = {"Giorgi": "1234", "Baiko": "1234", "Ani": "1234", "admin": "0000"}

st.set_page_config(page_title="Gemini 3 Smart Diary", layout="centered")

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
COLUMNS = ["თარიღი", "საათი", "ჩანაწერი", "განწყობა", "AI_პასუხი"]

if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(DB_FILE, sep='\t', index=False)

# --- ინტერფეისი ---
st.subheader("🎤 ისაუბრე ან ჩაწერე")

# 1. ხმოვანი შეყვანა
text_from_speech = speech_to_text(language='ka', start_prompt="🎤 ხმოვანი ჩაწერა", key='recorder')

# 2. ტექსტური ველი (უშუალო Key-ს გამოყენებით)
# თუ ხმამ რამე ჩაწერა, ის ხდება საწყისი მნიშვნელობა
user_input = st.text_area(
    "რა ხდება დღეს?", 
    value=text_from_speech if text_from_speech else "", 
    height=150, 
    key="diary_input"
)

# 3. შენახვის ღილაკი
if st.button("💾 შენახვა"):
    # ვიღებთ ტექსტს პირდაპირ ველის Key-დან
    content_to_save = st.session_state.diary_input
    
    if content_to_save:
        with st.spinner('Gemini 3 ფიქრობს...'):
            try:
                prompt = f"""
                მომხმარებელმა დაწერა: "{content_to_save}"
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
                
                # ინფორმაციის გაფილტვრა
                if "FIXED:" in res and "MOOD:" in res and "REPLY:" in res:
                    fixed = res.split("FIXED:")[1].split("| MOOD:")[0].strip()
                    mood = res.split("MOOD:")[1].split("| REPLY:")[0].strip()
                    reply = res.split("| REPLY:")[1].strip()
                else:
                    fixed, mood, reply = content_to_save, "ნეიტრალური", res
                
            except Exception as e:
                fixed, mood, reply = content_to_save, "შეცდომა", f"შეცდომა: {str(e)}"

            # ჩაწერა ფაილში
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
            
            st.success("წარმატებით შეინახა!")
            # მცირე პაუზა და გადატვირთვა ველის გასასუფთავებლად
            st.rerun()
    else:
        st.warning("გთხოვთ, ჯერ შეიყვანოთ ტექსტი.")

# --- ისტორია ---
st.divider()
try:
    df_hist = pd.read_csv(DB_FILE, sep='\t')
    if not df_hist.empty:
        for i, row in df_hist.sort_values(by=["თარიღი", "საათი"], ascending=False).iterrows():
            with st.expander(f"🗓️ {row['თარიღი']} | {row['საათი']} | {row['განწყობა']}"):
                st.write(f"✍️ **გასწორებული:** {row['ჩანაწერი']}")
                st.info(f"🤖 **AI:** {row['AI_პასუხი']}")
except:
    st.write("ჩანაწერები ჯერ არ არის.")
