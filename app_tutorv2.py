import streamlit as st
import pandas as pd
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from gtts import gTTS
import io
import os

# Tentativa de importação robusta para o ambiente Linux da nuvem
try:
    from google import genai
except ImportError:
    st.error("Dependência 'google-genai' não encontrada. Verifique se ela está no requirements.txt.")

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="AI English Executive Tutor", layout="wide", page_icon="🎓")

# --- SEGURANÇA: API KEY ---
# Certifique-se de adicionar GEMINI_API_KEY nos 'Secrets' do painel do Streamlit Cloud
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
else:
    st.error("API Key não encontrada. Adicione 'GEMINI_API_KEY' nos Secrets do Streamlit.")
    st.stop()

# --- FUNÇÕES DE PROCESSAMENTO DE ÁUDIO ---
def process_audio_to_text(audio_bytes):
    """Converte os bytes recebidos do mic_recorder em texto"""
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data, language="en-US")
        except sr.UnknownValueError:
            return "ERROR_UNDERSTAND"
        except sr.RequestError:
            return "ERROR_SERVICE"

def generate_voice_response(text):
    """Gera áudio via gTTS e exibe o player no navegador com autoplay"""
    tts = gTTS(text=text, lang='en', tld='com')
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    st.audio(audio_fp, format='audio/mp3', autoplay=True)

# --- INTERFACE DO USUÁRIO ---
st.title("🎓 AI English Executive Tutor")
st.markdown("---")

# Inicialização do Histórico
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

# Layout de Colunas: Chat e Dashboard
col_main, col_stats = st.columns([2, 1])

with col_main:
    st.subheader("🎙️ Voice Conversation")
    
    # Exibe histórico de mensagens
    for message in st.session_state.chat_log:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Componente de Gravação Web
    st.write("Click to speak with your tutor:")
    audio_data = mic_recorder(
        start_prompt="🎤 Start Recording",
        stop_prompt="🛑 Stop & Analyze",
        key='recorder'
    )

    if audio_data:
        user_text = process_audio_to_text(audio_data['bytes'])
        
        if user_text == "ERROR_UNDERSTAND":
            st.warning("I couldn't understand that. Could you please try again?")
        elif user_text == "ERROR_SERVICE":
            st.error("Speech service is temporarily unavailable.")
        elif user_text:
            # 1. Adiciona fala do usuário ao chat
            st.session_state.chat_log.append({"role": "user", "content": user_text})
            
            # 2. IA gera correção e resposta profissional
            prompt = f"""
            Analyze this sentence from an English student: '{user_text}'
            1. Correct grammar/vocabulary.
            2. Provide a 'Business Professional' alternative.
            3. Answer the student naturally.
            Keep it focused on Market Development/Executive context.
            """
            
            with st.spinner("Tutor is analyzing your speech..."):
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite-preview", 
                    contents=prompt
                )
                tutor_reply = response.text
            
            # 3. Adiciona resposta da IA ao chat
            st.session_state.chat_log.append({"role": "assistant", "content": tutor_reply})
            
            # 4. Atualiza a tela e fala a resposta
            st.rerun()
            generate_voice_response(tutor_reply)

with col_stats:
    st.subheader("📊 Session Insights")
    if len(st.session_state.chat_log) > 0:
        st.success(f"Interactions this session: {len(st.session_state.chat_log) // 2}")
        st.info("Tip: Use 'Market Trends' or 'Stakeholders' to enrich your business vocabulary.")
    else:
        st.write("Start a conversation to see your progress metrics.")

# Rodapé informacional
st.markdown("---")
st.caption("Powered by Gemini 3.1 & Streamlit Cloud | Optimized for Professional Growth")