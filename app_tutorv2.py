import streamlit as st
import pandas as pd
import io
import os
import tempfile

# --- ROBUST IMPORTS ---
try:
    from streamlit_mic_recorder import mic_recorder
    import speech_recognition as sr
    from gtts import gTTS
    from google import genai
except ImportError as e:
    st.error(f"Please wait a moment... The server is installing components: {e}")
    st.info("Tip: If this error persists for more than 2 minutes, click 'Reboot App' in the Streamlit Cloud panel.")
    st.stop()

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Executive Tutor", layout="wide", page_icon="🎓")

# --- GEMINI CONNECTION VIA SECRETS ---
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Error: Please configure 'GEMINI_API_KEY' in Streamlit Secrets.")
    st.stop()

# --- CORE FUNCTIONS ---
def process_audio_from_wav_bytes(wav_bytes: bytes, language: str = "en-US"):
    """
    Converts WAV bytes to text using SpeechRecognition.
    Saves to a temporary file for maximum compatibility.
    """
    if not wav_bytes or len(wav_bytes) == 0:
        return None

    recognizer = sr.Recognizer()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(wav_bytes)
        tmp_path = tmp.name

    try:
        with sr.AudioFile(tmp_path) as source:
            audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data, language=language)
    except sr.UnknownValueError:
        return None
    except Exception:
        return None
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

def text_to_speech(text: str, lang: str = "en"):
    """Generates audio with gTTS and displays the player."""
    if not text:
        return

    try:
        # Using 'co.uk' for a British accent which tends to sound slightly more natural
        tts = gTTS(text=text, lang=lang, tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        st.audio(fp, format='audio/mp3', autoplay=True)
        st.caption("🔈 If audio doesn't play automatically, please click the play button (browsers often block autoplay).")
    except Exception:
        st.warning("Could not generate voice response at this time.")

def run_tutor(user_text: str):
    """Calls Gemini with a structured prompt and returns the response."""
    # The prompt is now instructing the AI to communicate exclusively in English
    prompt = f"""
You are a highly professional English Tutor specialized in Business English and Market Development.
The student said: '{user_text}'.

Your Task:
1. Review the input for grammar and vocabulary mistakes.
2. Suggest a more 'Executive/Business Professional' way to phrase it.
3. Reply to the content naturally in English to keep the conversation flowing.

Context: The student is a Market Development Analyst interacting with teams in China. 
Instruction: Provide the feedback and the reply clearly in English.
"""
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt
        )
        return getattr(response, "text", "").strip()
    except Exception:
        st.error("I couldn't reach the AI model. Please try again in a moment.")
        return None

# --- INITIAL STATE ---
st.title("🎓 AI English Executive Tutor")
st.caption("Focus: Market Development & Negotiations with China Team.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.divider()

# --- AUDIO CAPTURE PANEL ---
st.write("### 🎙️ Practice your speech")

audio_input = mic_recorder(
    start_prompt="🎤 Start Speaking",
    stop_prompt="🛑 Stop & Send",
    just_once=True,
    use_container_width=True,
    format="wav",
    key="recorder"
)

# File uploader fallback
uploaded = st.file_uploader(
    "Or upload an audio file (WAV/AIFF/FLAC)",
    type=["wav", "aiff", "aif", "flac"]
)

# --- MANUAL TEXT INPUT ---
manual_text = st.chat_input("Or type your message here:")

def handle_user_text(user_text: str):
    if not user_text:
        return
    st.session_state.messages.append({"role": "user", "content": user_text})

    with st.spinner("Analyzing your speech..."):
        tutor_reply = run_tutor(user_text)

    if tutor_reply:
        st.session_state.messages.append({"role": "assistant", "content": tutor_reply})
        with st.chat_message("assistant"):
            st.markdown(tutor_reply)
            text_to_speech(tutor_reply)

# --- WORKFLOWS ---
if audio_input and isinstance(audio_input, dict):
    fmt = audio_input.get("format", "wav")
    wav_bytes = audio_input.get("bytes", b"")

    if fmt != "wav":
        st.warning("Recorder returned non-WAV format. Please record again or upload a WAV file.")
    else:
        user_text = process_audio_from_wav_bytes(wav_bytes, language="en-US")
        if user_text:
            handle_user_text(user_text)
        else:
            st.warning("I couldn't process your audio. Please speak closer to the mic or check browser permissions.")

if uploaded is not None:
    file_bytes = uploaded.read()
    user_text = process_audio_from_wav_bytes(file_bytes, language="en-US")
    if user_text:
        handle_user_text(user_text)
    else:
        st.warning("Could not recognize speech in this file. Ensure it is a clear WAV/AIFF/FLAC file.")

if manual_text:
    handle_user_text(manual_text)

# --- SIDEBAR ---
with st.sidebar:
    st.header("📊 Current Session")
    interactions = sum(1 for m in st.session_state.messages if m["role"] == "assistant")
    st.write(f"Completed interactions: {interactions}")
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()