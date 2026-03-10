import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
from gtts import gTTS
import pygame
from google import genai
import os
import time
from datetime import datetime

# --- CONFIGURAÇÃO E BANCO DE DADOS ---
st.set_page_config(page_title="AI Executive Tutor", layout="wide", page_icon="🎓")

# Inicializa o banco de dados (SQLite já é nativo do Python)
def init_db():
    conn = sqlite3.connect('learning_memory.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS progress 
                 (date TEXT, original TEXT, correction TEXT, category TEXT)''')
    conn.commit()
    return conn

conn = init_db()
client = genai.Client(api_key="GEMINI_API_KEY") # Coloque sua chave válida

# --- ESTILIZAÇÃO E DASHBOARD ---
st.title("🎓 English Executive Tutor")
st.markdown("---")

tab1, tab2 = st.tabs(["🎙️ Practice Session", "📊 Progress Report"])

# --- LÓGICA DE ÁUDIO (SEM PYAUDIO) ---
def speak(text):
    tts = gTTS(text=text, lang='en', tld='com')
    tts.save("response.mp3")
    pygame.mixer.init()
    pygame.mixer.music.load("response.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy(): time.sleep(0.1)
    pygame.mixer.quit()
    if os.path.exists("response.mp3"): os.remove("response.mp3")

def record_speech():
    fs = 44100
    duration = 5 # segundos (podemos ajustar para dinâmico depois)
    st.warning("Listening for 5 seconds...")
    rec = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    write('output.wav', fs, rec)
    
    recognizer = sr.Recognizer()
    with sr.AudioFile('output.wav') as source:
        audio = recognizer.record(source)
        try: return recognizer.recognize_google(audio, language="en-US")
        except: return None

# --- CONTEÚDO DAS ABAS ---
with tab1:
    if st.button("🎤 Talk to Tutor"):
        user_input = record_speech()
        if user_input:
            st.chat_message("user").write(user_input)
            
            # IA como Professor
            prompt = f"As an English Tutor, analyze: '{user_input}'. 1. Correct it. 2. Explain why. 3. Answer naturally."
            response = client.models.generate_content(model="gemini-3.1-flash-lite-preview", contents=prompt)
            
            st.chat_message("assistant").write(response.text)
            
            # Salva no Banco de Dados para o Relatório
            c = conn.cursor()
            c.execute("INSERT INTO progress VALUES (?, ?, ?, ?)", 
                      (datetime.now().strftime("%Y-%m-%d"), user_input, response.text[:100], "Practice"))
            conn.commit()
            
            speak(response.text)
        else:
            st.error("Could not hear you. Please try again.")

with tab2:
    st.header("Your Learning Journey")
    df = pd.read_sql_query("SELECT * FROM progress", conn)
    
    if not df.empty:
        # Gráfico simples de progresso
        st.line_chart(df.groupby('date').size())
        st.write("### Recent Corrections")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Start practicing to see your statistics!")