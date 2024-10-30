import streamlit as st
import asyncio
from shazamio import Shazam
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import os
import uuid
from datetime import timedelta

# Configuración de la página con tema oscuro
st.set_page_config(
    page_title="Music Detective",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .stApp {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    .main {
        background-color: #1a1a1a;
    }
    
    .stButton>button {
        width: 100%;
        background-color: #ff4b4b !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
    }
    
    .status-card {
        background-color: #2d2d2d;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .status-card.green {
        background-color: rgba(47, 132, 90, 0.2);
        border-left: 4px solid #2f845a;
    }
    
    .status-card.yellow {
        background-color: rgba(255, 191, 0, 0.2);
        border-left: 4px solid #ffbf00;
    }
    
    .song-card {
        background-color: #2d2d2d;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    h1, h2, h3 {
        color: #ff4b4b !important;
    }
    
    .upload-section {
        background-color: #2d2d2d;
        border-radius: 10px;
        padding: 2rem;
        margin: 1rem 0;
        border: 2px dashed #404040;
    }
    
    .stProgress > div > div > div {
        background-color: #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

# Título y descripción
st.markdown("<h1 style='text-align: center;'>🎵 Music Detective</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888888;'>Descubre las canciones que hay en tus videos favoritos</p>", unsafe_allow_html=True)

def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path, codec='mp3')
    video.close()

def split_audio(audio_path, fragment_length=12):
    audio = AudioSegment.from_mp3(audio_path)
    duration_seconds = len(audio) / 1000
    fragments = []
    total_fragments = len(range(0, len(audio), fragment_length * 1000))
    
    for i, start_ms in enumerate(range(0, len(audio), fragment_length * 1000)):
        end_ms = start_ms + fragment_length * 1000
        fragment = audio[start_ms:end_ms]
        fragment_filename = f"fragment_{uuid.uuid4().hex}.mp3"
        fragment.export(fragment_filename, format="mp3")
        fragments.append(fragment_filename)
        
        # Actualizar mensaje de progreso en lugar de usar barra
        progress = (i + 1) / total_fragments
        st.text(f"Procesando fragmento {i + 1} de {total_fragments} ({int(progress * 100)}%)")
    
    return fragments

async def recognize_song(shazam, fragment_path, start_time):
    out = await shazam.recognize_song(fragment_path)
    if out and 'track' in out:
        track = out['track']
        return {
            "title": track['title'],
            "subtitle": track['subtitle'],
            "shazam_url": track['url'],
            "timestamp": str(timedelta(seconds=start_time))
        }
    return None

def process_video(video_file):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="status-card green">
                <h3>📊 Estadísticas del Proceso</h3>
                <p>Seguimiento en tiempo real del análisis</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="status-card yellow">
                <h3>⚡ Estado del Proceso</h3>
                <p>Información sobre el progreso actual</p>
            </div>
        """, unsafe_allow_html=True)

    unique_id = uuid.uuid4().hex
    video_filename = f"uploaded_{unique_id}.mp4"
    audio_filename = f"extracted_{unique_id}.mp3"

    with open(video_filename, "wb") as f:
        f.write(video_file.getbuffer())

    st.markdown('<div class="status-card">🎥 Extrayendo audio del video...</div>', unsafe_allow_html=True)
    extract_audio(video_filename, audio_filename)
    
    st.markdown('<div class="status-card">🔍 Dividiendo audio en fragmentos...</div>', unsafe_allow_html=True)
    fragments = split_audio(audio_filename)
    
    shazam = Shazam()
    detected_songs = []

    async def recognize_all():
        total_fragments = len(fragments)
        for idx, fragment in enumerate(fragments):
            start_time = idx * 12
            song = await recognize_song(shazam, fragment, start_time)
            if song:
                detected_songs.append(song)
                st.markdown(f"""
                    <div class="song-card">
                        <div style="color: #ff4b4b; font-size: 1.2rem;">🎵 {song['title']}</div>
                        <div style="color: #888888;">👤 {song['subtitle']}</div>
                        <div style="color: #666666;">⏱️ {song['timestamp']}</div>
                    </div>
                """, unsafe_allow_html=True)
            st.text(f"Analizando fragmento {idx + 1} de {total_fragments}")
            os.remove(fragment)

    asyncio.run(recognize_all())

    # Limpieza
    os.remove(video_filename)
    os.remove(audio_filename)

    # Resultados finales
    if detected_songs:
        st.markdown("## 🎸 Canciones Detectadas")
        for song in detected_songs:
            st.markdown(f"""
                <div class="song-card">
                    <div style="color: #ff4b4b; font-size: 1.2rem;">🎵 {song['title']}</div>
                    <div style="color: #888888;">👤 {song['subtitle']}</div>
                    <div style="color: #666666;">⏱️ {song['timestamp']}</div>
                    <a href="{song['shazam_url']}" target="_blank" 
                       style="display: inline-block; margin-top: 0.5rem; padding: 0.5rem 1rem; 
                              background-color: #ff4b4b; color: white; text-decoration: none; 
                              border-radius: 5px;">
                        Ver en Shazam 🔗
                    </a>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-card">❌ No se detectaron canciones en el video.</div>', unsafe_allow_html=True)

# Sección de carga de archivo
st.markdown("""
    <div class="upload-section">
        <h3 style="margin-bottom: 1rem;">📤 Sube tu Video</h3>
        <p style="color: #888888;">Formatos soportados: MP4, MOV, AVI, MKV</p>
    </div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("🔍 Detectar Canciones"):
        process_video(uploaded_file)
