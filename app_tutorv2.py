import streamlit as st
import pandas as pd
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from gtts import gTTS
import io
import os

# --- TENTATIVA DE IMPORTAÇÃO ROBUSTA (Resolve o erro ModuleNotFoundError) ---
try:
    from google import genai
except ImportError:
    try:
        import google.genai as genai
    except ImportError:
        st.error("As bibliotecas do Google ainda estão sendo instaladas no servidor. Aguarde 1 minuto e atualize a página.")
        st.stop()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="AI English Executive Tutor", layout="wide", page_icon="🎓")

# --- CONEXÃO COM GEMINI (VIA SECRETS) ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
else:
    st.error("Erro: Configure 'GEMINI_API_KEY' nos Secrets do painel do Streamlit Cloud.")
    st.stop()

# --- FUNÇÕES DE ÁUDIO ---
def process_audio(audio_bytes):
    """Converte áudio do navegador em texto"""
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data, language="en-US")
        except:
            return None

def speak_response(text):
    """Gera voz e exibe o player com autoplay"""
    try:
        tts = gTTS(text=text, lang='en', tld='com')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3', autoplay=True)
    except Exception as e:
        st.warning("Ocorreu um erro ao gerar a voz, mas você pode ler a resposta abaixo.")

# --- INTERFACE ---
st.title("🎓 AI English Executive Tutor")
st.caption("Focado em Desenvolvimento de Mercado e Reuniões com o Time da China.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibição do Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.divider()

# GRAVADOR WEB
st.write("### 🎙️ Fale com o Tutor")
audio_input = mic_recorder(
    start_prompt="Clique para falar",
    stop_prompt="Parar e Analisar",
    key='recorder'
)

if audio_input:
    user_text = process_audio(audio_input['bytes'])
    
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        
        # Prompt Estruturado para o Gemini
        prompt = f"""
        Você é um tutor de inglês para executivos. 
        Analise a frase: '{user_text}'.
        1. Corrija erros gramaticais.
        2. Sugira uma versão mais profissional (Business English).
        3. Responda à frase de forma natural para manter a conversa.
        Contexto: O aluno trabalha com desenvolvimento de mercado e lida com times na China.
        """
        
        with st.spinner("O Tutor está analisando sua fala..."):
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview", 
                contents=prompt
            )
            tutor_reply = response.text
        
        st.session_state.messages.append({"role": "assistant", "content": tutor_reply})
        st.rerun() # Atualiza para exibir a conversa
        speak_response(tutor_reply)
    else:
        st.warning("Não consegui entender o áudio. Tente falar novamente mais perto do microfone.")