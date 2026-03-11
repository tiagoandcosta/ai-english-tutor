import streamlit as st
import pandas as pd
import io
import os

# --- IMPORTAÇÃO ROBUSTA ---
try:
    from streamlit_mic_recorder import mic_recorder
    import speech_recognition as sr
    from gtts import gTTS
    from google import genai
except ImportError as e:
    st.error(f"Aguarde um momento... O servidor está instalando os componentes: {e}")
    st.info("Dica: Se este erro persistir por mais de 2 minutos, clique em 'Reboot App' no painel do Streamlit.")
    st.stop()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="AI Executive Tutor", layout="wide", page_icon="🎓")

# Conexão com Gemini via Secrets
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Erro: Configure 'GEMINI_API_KEY' nos Secrets do Streamlit Cloud.")
    st.stop()

# --- FUNÇÕES CORE ---
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

def text_to_speech(text):
    """Gera áudio e exibe o player com autoplay"""
    try:
        tts = gTTS(text=text, lang='en', tld='com')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3', autoplay=True)
    except Exception as e:
        st.warning("Não foi possível gerar a voz no momento.")

# --- INTERFACE ---
st.title("🎓 AI English Executive Tutor")
st.caption("Focado em Desenvolvimento de Mercado e Negociações com a China.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibição do Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.divider()

# GRAVADOR WEB
st.write("### 🎙️ Pratique sua fala:")
audio_input = mic_recorder(
    start_prompt="🎤 Começar a Falar",
    stop_prompt="🛑 Parar e Enviar",
    key='recorder'
)

if audio_input:
    user_text = process_audio(audio_input['bytes'])
    
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        
        # Prompt Estruturado para o Contexto do Usuário
        prompt = f"""
        Você é um tutor de inglês especializado em Business English e Market Development.
        O aluno disse: '{user_text}'.
        
        Sua tarefa:
        1. Corrija gramática e pronúncia (se aplicável ao texto).
        2. Sugira uma forma mais executiva/profissional de dizer o mesmo.
        3. Responda à pergunta ou comentário de forma natural em inglês para manter o diálogo.
        
        Contexto: O aluno interage com times na China e busca crescimento de mercado.
        """
        
        with st.spinner("Analisando sua fala..."):
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview", 
                contents=prompt
            )
            tutor_reply = response.text
        
        st.session_state.messages.append({"role": "assistant", "content": tutor_reply})
        st.rerun()
        text_to_speech(tutor_reply)
    else:
        st.warning("Não consegui processar seu áudio. Tente falar mais perto do microfone ou verifique as permissões do navegador.")

# Dashboard Lateral Simples
with st.sidebar:
    st.header("📊 Sessão Atual")
    st.write(f"Interações: {len(st.session_state.messages) // 2}")
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()