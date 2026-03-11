import streamlit as st
import pandas as pd
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from gtts import gTTS
import io
import os

# Tenta importar o SDK do Google, tratando possíveis erros de namespace na nuvem
try:
    from google import genai
except ImportError:
    st.error("Erro de dependência: O módulo 'google-genai' não foi encontrado. Verifique seu requirements.txt.")

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="AI Executive Tutor", layout="wide", page_icon="🎓")

# --- CONEXÃO COM GEMINI (VIA SECRETS) ---
# Certifique-se de ter configurado GEMINI_API_KEY no painel do Streamlit Cloud
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("Erro de Chave API: Configure 'GEMINI_API_KEY' nos Secrets do Streamlit.")
    st.stop()

# --- FUNÇÕES DE ÁUDIO ---
def process_audio(audio_bytes):
    """Converte os bytes do microfone em texto usando Google Speech Recognition"""
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data, language="en-US")
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError:
            return "Speech service error"

def text_to_speech_web(text):
    """Gera o áudio da resposta e exibe o player com autoplay"""
    try:
        tts = gTTS(text=text, lang='en', tld='com')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3', autoplay=True)
    except Exception as e:
        st.warning("Não foi possível gerar a voz, mas você pode ler a resposta abaixo.")

# --- INTERFACE E LOGICA ---
st.title("🎓 AI English Executive Tutor")
st.caption("Preparing you for international meetings and market development.")

# Inicializa o histórico do chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Aba Lateral: Dashboard de Progresso (Simulado por enquanto)
with st.sidebar:
    st.header("📊 Learning Progress")
    st.write("Current Session Stats:")
    st.metric("Words Practiced", len(st.session_state.messages) * 12)
    st.info("Tip: Focus on using 'contractions' like I'm, don't, and we're to sound more natural.")

# Exibe as mensagens do chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.divider()

# GRAVADOR DE VOZ (Interface Web)
st.write("### 🎙️ Practice Now")
audio_input = mic_recorder(
    start_prompt="Click to Start Speaking",
    stop_prompt="Stop and Analyze",
    key='recorder'
)

if audio_input:
    user_text = process_audio(audio_input['bytes'])
    
    if user_text and user_text not in ["Could not understand audio", "Speech service error"]:
        # 1. Mostra o que o usuário disse
        st.session_state.messages.append({"role": "user", "content": user_text})
        
        # 2. Chama o Gemini 3.1 para correção e resposta
        prompt = f"""
        Role: Professional English Tutor.
        User Input: '{user_text}'
        Task: 
        1. Correct any grammar mistakes.
        2. Suggest a 'Business English' version for a meeting.
        3. Answer the question or continue the talk.
        Format: Keep it concise and encouraging.
        """
        
        with st.spinner("Tutor is thinking..."):
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview", 
                contents=prompt
            )
            tutor_reply = response.text
        
        # 3. Guarda e exibe a resposta
        st.session_state.messages.append({"role": "assistant", "content": tutor_reply})
        st.rerun() # Atualiza para mostrar a conversa
        
        # 4. Fala a resposta
        text_to_speech_web(tutor_reply)
    else:
        st.warning("I couldn't hear you clearly. Please try again!")