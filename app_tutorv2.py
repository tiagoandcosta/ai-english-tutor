import streamlit as st
import pandas as pd
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from gtts import gTTS
from google import genai
import io
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="AI English Tutor", layout="wide")

# Puxa a chave dos "Secrets" do Streamlit (Configuraremos no dashboard da nuvem)
api_key = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=api_key)

# --- FUNÇÕES DE ÁUDIO WEB ---
def process_audio(audio_bytes):
    """Converte os bytes do microfone em texto"""
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data, language="en-US")
        except:
            return None

def text_to_speech_web(text):
    """Gera áudio e exibe o player no navegador"""
    tts = gTTS(text=text, lang='en', tld='com')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp, format='audio/mp3', autoplay=True)

# --- INTERFACE ---
st.title("🎓 AI English Executive Tutor")
st.info("Preparing you for meetings with the China Team.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Aba lateral para o seu Relatório (Dashboard)
st.sidebar.title("📊 Progress Report")
# Aqui futuramente conectaremos o banco de dados persistente

# Área de Conversação
st.write("### Conversation")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# O GRAVADOR WEB (Substitui o botão de áudio antigo)
audio = mic_recorder(
    start_prompt="🎤 Start Speaking",
    stop_prompt="🛑 Stop & Send",
    key='recorder'
)

if audio:
    user_text = process_audio(audio['bytes'])
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        
        # Chamada ao Gemini 3.1
        prompt = f"As a business English tutor, analyze: '{user_text}'. Correct it and answer naturally."
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview", 
            contents=prompt
        )
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun() # Atualiza a tela para mostrar a resposta
        text_to_speech_web(response.text)