import streamlit as st
import pandas as pd  # (mantido se você quiser usar depois)
import io
import os
import tempfile

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

# --- CONEXÃO COM GEMINI VIA SECRETS ---
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Erro: Configure 'GEMINI_API_KEY' nos Secrets do Streamlit Cloud.")
    st.stop()

# --- FUNÇÕES CORE ---
def process_audio_from_wav_bytes(wav_bytes: bytes, language: str = "en-US"):
    """
    Converte bytes WAV (PCM) em texto usando SpeechRecognition.
    Salva em um arquivo temporário .wav para compatibilidade máxima.
    """
    if not wav_bytes or len(wav_bytes) == 0:
        return None

    recognizer = sr.Recognizer()

    # Cria arquivo temporário WAV para o AudioFile (mais robusto do que BytesIO em alguns ambientes)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(wav_bytes)
        tmp_path = tmp.name

    try:
        with sr.AudioFile(tmp_path) as source:
            audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data, language=language)
    except sr.UnknownValueError:
        return None
    except Exception as e:
        # Log opcional: st.debug/print
        return None
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def text_to_speech(text: str, lang: str = "en"):
    """Gera áudio com gTTS e exibe o player (com autoplay se o navegador permitir)."""
    if not text:
        return

    try:
        tts = gTTS(text=text, lang=lang, tld='com')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)  # IMPORTANTE: reposiciona o ponteiro antes de tocar
        st.audio(fp, format='audio/mp3', autoplay=True)
        st.caption("🔈 Se o áudio não tocar automaticamente, clique no player (os navegadores bloqueiam autoplay até alguma interação).")
    except Exception:
        st.warning("Não foi possível gerar a voz no momento.")


def run_tutor(user_text: str):
    """Chama o Gemini com o prompt estruturado e retorna a resposta."""
    prompt = f"""
Você é um tutor de inglês especializado em Business English e Market Development.
O aluno disse: '{user_text}'.

Sua tarefa:
1. Corrija gramática e pronúncia (se aplicável ao texto).
2. Sugira uma forma mais executiva/profissional de dizer o mesmo.
3. Responda à pergunta ou comentário de forma natural em inglês para manter o diálogo.

Contexto: O aluno interage com times na China e busca crescimento de mercado.
"""
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt
        )
        return getattr(response, "text", "").strip()
    except Exception as e:
        st.error("Não consegui obter resposta do modelo agora. Tente novamente em instantes.")
        return None


# --- ESTADO INICIAL ---
st.title("🎓 AI English Executive Tutor")
st.caption("Focado em Desenvolvimento de Mercado e Negociações com a China.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibir histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.divider()

# --- PAINEL DE CAPTURA DE ÁUDIO ---
st.write("### 🎙️ Pratique sua fala")

# Força o retorno em WAV (evita o erro do SpeechRecognition com WEBM/OPUS)
audio_input = mic_recorder(
    start_prompt="🎤 Começar a Falar",
    stop_prompt="🛑 Parar e Enviar",
    just_once=True,                # evita reprocessar o mesmo áudio em cada rerun
    use_container_width=True,
    format="wav",                  # <<< ESSENCIAL: retorna WAV PCM
    key="recorder"
)

# Fallback: upload de arquivo WAV/AIFF/FLAC
uploaded = st.file_uploader(
    "Ou envie um arquivo de áudio (WAV/AIFF/FLAC)",
    type=["wav", "aiff", "aif", "flac"]
)

# --- CAPTURA DE TEXTO MANUAL (opcional) ---
manual_text = st.chat_input("Ou digite sua mensagem em inglês (ou português):")

def handle_user_text(user_text: str, tts_lang: str = "en"):
    if not user_text:
        return
    st.session_state.messages.append({"role": "user", "content": user_text})

    with st.spinner("Analisando sua fala..."):
        tutor_reply = run_tutor(user_text)

    if tutor_reply:
        st.session_state.messages.append({"role": "assistant", "content": tutor_reply})
        # Render imediatamente (sem st.rerun, para permitir tocar TTS abaixo)
        with st.chat_message("assistant"):
            st.markdown(tutor_reply)
            text_to_speech(tutor_reply, lang=tts_lang)


# --- FLUXO POR ÁUDIO ---
if audio_input and isinstance(audio_input, dict):
    fmt = audio_input.get("format", "wav")
    wav_bytes = audio_input.get("bytes", b"")

    if fmt != "wav":
        st.warning("O gravador retornou um formato diferente de WAV. Regrave ou envie um arquivo WAV/AIFF/FLAC.")
    else:
        # Reconhece em inglês por padrão; se quiser PT-BR mude para "pt-BR"
        user_text = process_audio_from_wav_bytes(wav_bytes, language="en-US")

        if user_text:
            handle_user_text(user_text, tts_lang="en")
        else:
            st.warning("Não consegui processar seu áudio. Tente falar mais perto do microfone ou verifique as permissões do navegador.")

# --- FLUXO POR UPLOAD ---
if uploaded is not None:
    file_bytes = uploaded.read()
    # Tenta reconhecer como inglês (ajuste se quiser)
    user_text = process_audio_from_wav_bytes(file_bytes, language="en-US")
    if user_text:
        handle_user_text(user_text, tts_lang="en")
    else:
        st.warning("Não consegui reconhecer fala neste arquivo. Verifique se é PCM WAV/AIFF/FLAC com voz audível.")

# --- FLUXO POR TEXTO MANUAL ---
if manual_text:
    # Se estiver em PT, você pode traduzir antes, mas aqui mantemos simples:
    handle_user_text(manual_text, tts_lang="en")


# --- SIDEBAR ---
with st.sidebar:
    st.header("📊 Sessão Atual")
    # cada par (user, assistant) conta 1
    pares = sum(1 for m in st.session_state.messages if m["role"] == "assistant")
    st.write(f"Interações: {pares}")
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()