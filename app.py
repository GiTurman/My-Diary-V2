import streamlit as st
import google.generativeai as genai
from datetime import datetime
import pandas as pd
import os
from streamlit_mic_recorder import speech_to_text

# --- კონფიგურაცია ---
API_KEY = "AIzaSyAgZjH7-PPa8zcHfU2d5oSaiHFEKbkyBG8"
genai.configure(api_key=API_KEY)

USERS = {"giorgi": "1234","Baiko": "1234", "Ani": "1234", "admin": "0000"}

st.set_page_config(page_title="AI Research Diary", layout="centered")

# --- ავტორიზაცია ---
if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"] is None:
    st.title("🔐 შესვლა")
    username = st.text_input("მომხმარებელი:")
    password = st.text_input("პაროლი:", type="password")
    if st.button("შესვლა"):
        if username in USERS and USERS[username] == password:
            st.session_state["user"] = username
            st.rerun()
        else:
            st.error("არასწორი მონაცემები!")
    st.stop()

current_user = st.session_state["user"]
st.title(f"🚀 {current_user}-ს ინტელექტუალური დღიური")

# --- მონაცემთა ბაზის გამართვა ---
DB_FILE = f"diary_{current_user}.csv"
COLUMNS = ["თარიღი", "საათი", "ჩანაწერი", "განწყობა", "AI_პასუხი"]

def load_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame(columns=COLUMNS)
    try:
        # ვიყენებთ sep='\t' (Tab), რომ მძიმეებმა არ აურიოს ცხრილი
        return pd.read_csv(DB_FILE, sep='\t')
    except:
        return pd.DataFrame(columns=COLUMNS)

# --- ინტერფეისი ---
st.subheader("🎤 ჩაწერე ან ისაუბრე")
text_from_speech = speech_to_text(language='ka', start_prompt="ჩაწერა (ისაუბრე)", key='recorder')
user_input = st.text_area("რა ხდება?", value=text_from_speech if text_from_speech else "", height=100)

if st.button("💾 შენახვა და AI ძიება"):
    if user_input:
        with st.spinner('Gemini იძიებს...'):
            sentiment = "ანალიზი..."
            ai_response = "..."
            
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""
                შენ ხარ პირადი ასისტენტი. მომხმარებელმა დაწერა: "{user_input}"
                1. თუ არის კითხვა, უპასუხე დეტალურად.
                2. თუ არის ჩანაწერი, გაუკეთე ანალიზი.
                3. განსაზღვრე განწყობა (1 სიტყვა).
                დააბრუნე ფორმატით: SENTIMENT: [განწყობა] | ANSWER: [პასუხი]
                """
                response = model.generate_content(prompt)
                res_text = response.text
                
                if "SENTIMENT:" in res_text and "ANSWER:" in res_text:
                    sentiment = res_text.split("SENTIMENT:")[1].split("| ANSWER:")[0].strip()
                    ai_response = res_text.split("| ANSWER:")[1].strip()
                else:
                    ai_response = res_text
            except Exception as e:
                sentiment = "შეცდომა"
                ai_response = f"AI დროებით მიუწვდომელია. (შეცდომა: {e})"

            # შენახვა
            now = datetime.now()
            new_row = pd.DataFrame([[
                now.strftime("%Y-%m-%d"), 
                now.strftime("%H:%M"), 
                user_input.replace('\t', ' '), # Tab-ის მოცილება ტექსტიდან
                sentiment, 
                ai_response.replace('\t', ' ')
            ]], columns=COLUMNS)
            
            df = load_data()
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DB_FILE, sep='\t', index=False)
            
            st.success("შენახულია!")
            st.rerun()

st.divider()

# --- ისტორიის ჩვენება ---
df_history = load_data()
if not df_history.empty:
    st.subheader("📚 ჩანაწერების არქივი")
    for i, row in df_history.sort_values(by=["თარიღი", "საათი"], ascending=False).iterrows():
        with st.expander(f"🗓️ {row['თარიღი']} | 🕒 {row['საათი']} | {row['განწყობა']}"):
            st.write(f"**ჩანაწერი:** {row['ჩანაწერი']}")
            st.info(f"🤖 **AI პასუხი:**\n\n{row['AI_პასუხი']}")
