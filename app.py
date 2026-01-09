import streamlit as st
import google.generativeai as genai
from datetime import datetime
import pandas as pd
import os
from streamlit_mic_recorder import speech_to_text

# --- კონფიგურაცია ---
API_KEY = "AIzaSyAgZjH7-PPa8zcHfU2d5oSaiHFEKbkyBG8" # <--- აუცილებლად შეცვალე!
genai.configure(api_key=API_KEY)

USERS = {"giorgi": "1234", "admin": "0000"}

st.set_page_config(page_title="AI Smart Diary", layout="centered")

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

# --- მონაცემთა ბაზა ---
DB_FILE = f"diary_{current_user}.csv"
COLUMNS = ["თარიღი", "საათი", "ჩანაწერი", "განწყობა", "AI_პასუხი"]

def load_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame(columns=COLUMNS)
    try:
        return pd.read_csv(DB_FILE, sep='\t')
    except:
        return pd.DataFrame(columns=COLUMNS)

# --- ინტერფეისი ---
st.subheader("🎤 ჩაწერე ან ისაუბრე")
text_from_speech = speech_to_text(language='ka', start_prompt="ჩაწერა (ისაუბრე)", key='recorder')
user_input = st.text_area("რა ხდება?", value=text_from_speech if text_from_speech else "", height=100)

if st.button("💾 შენახვა და AI დამუშავება"):
    if user_input:
        with st.spinner('Gemini ასწორებს ტექსტს და პასუხობს...'):
            sentiment = "ანალიზი..."
            ai_response = "..."
            processed_text = user_input # თუ AI-მ ვერ უპასუხა, დატოვებს ორიგინალს
            
            try:
                # ვიყენებთ gemini-pro-ს, რომელიც ყველაზე სტაბილურია
                model = genai.GenerativeModel('gemini-pro')
                
                prompt = f"""
                შენ ხარ ტექსტის რედაქტორი და ასისტენტი.
                მომხმარებელმა დაწერა: "{user_input}"
                
                დავალება:
                1. გაასწორე ეს ტექსტი გრამატიკულად: დაამატე მძიმეები, წერტილები და კითხვის ნიშნები (ქართულად).
                2. თუ არის კითხვა ამინდზე ან სხვა რამეზე, უპასუხე მოკლედ.
                3. განსაზღვრე განწყობა (1 სიტყვა).
                
                დააბრუნე ფორმატით:
                FIXED_TEXT: [აქ გასწორებული ტექსტი]
                SENTIMENT: [განწყობა]
                ANSWER: [ასისტენტის პასუხი]
                """
                
                response = model.generate_content(prompt)
                res_text = response.text
                
                if "FIXED_TEXT:" in res_text and "SENTIMENT:" in res_text:
                    processed_text = res_text.split("FIXED_TEXT:")[1].split("SENTIMENT:")[0].strip()
                    sentiment = res_text.split("SENTIMENT:")[1].split("ANSWER:")[0].strip()
                    ai_response = res_text.split("ANSWER:")[1].strip()
                else:
                    ai_response = res_text
            except Exception as e:
                st.error(f"AI კავშირის შეცდომა. შეამოწმე API Key! ({e})")
                sentiment = "AI შეცდომა"
                ai_response = "ვერ მოხერხდა AI-სთან დაკავშირება."

            # შენახვა (ვიყენებთ გასწორებულ ტექსტს!)
            now = datetime.now()
            new_row = pd.DataFrame([[
                now.strftime("%Y-%m-%d"), 
                now.strftime("%H:%M"), 
                processed_text.replace('\t', ' '), 
                sentiment, 
                ai_response.replace('\t', ' ')
            ]], columns=COLUMNS)
            
            df = load_data()
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DB_FILE, sep='\t', index=False)
            
            st.success("ჩანაწერი გასწორდა და შენახულია!")
            st.rerun()

st.divider()

# --- ისტორია ---
df_history = load_data()
if not df_history.empty:
    st.subheader("📚 ჩანაწერების არქივი")
    for i, row in df_history.sort_values(by=["თარიღი", "საათი"], ascending=False).iterrows():
        with st.expander(f"🗓️ {row['თარიღი']} | 🕒 {row['საათი']} | {row['განწყობა']}"):
            st.write(f"**გასწორებული ტექსტი:** {row['ჩანაწერი']}")
            st.info(f"🤖 **AI პასუხი:**\n\n{row['AI_პასუხი']}")
