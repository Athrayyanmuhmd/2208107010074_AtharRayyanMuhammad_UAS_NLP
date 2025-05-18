import os
import tempfile
import requests
import gradio as gr
import scipy.io.wavfile
import time
import numpy as np
import base64

# Konfigurasi API endpoint
API_URL = "http://localhost:8000/voice-chat"

def decode_base64(b64_text):
    """Decode teks base64 ke UTF-8"""
    if not b64_text:
        return ""
    try:
        return base64.b64decode(b64_text).decode('utf-8')
    except:
        return "Error: Tidak dapat mendekode teks"

def translate_to_indonesian(english_text):
    """
    Fungsi sederhana untuk menerjemahkan frasa umum dari bahasa Inggris ke Indonesia
    untuk keperluan demonstrasi
    """
    # Dictionary terjemahan sederhana
    translations = {
        "what": "apa",
        "is": "adalah",
        "are": "adalah",
        "the": "",
        "from": "dari",
        "latin": "latin",
        "durian": "durian",
        "name": "nama",
        "of": "dari",
        "fruit": "buah",
        "how": "bagaimana",
        "to": "untuk",
        "who": "siapa",
        "where": "dimana",
        "when": "kapan",
        "why": "mengapa",
        "can": "bisakah",
        "you": "kamu",
        "i": "saya",
        "we": "kami",
        "they": "mereka",
        "he": "dia",
        "she": "dia",
        "it": "itu",
        "this": "ini",
        "that": "itu",
        "for": "untuk",
        "and": "dan",
        "or": "atau",
        "not": "tidak",
        "yes": "ya",
        "no": "tidak",
        "hello": "halo",
        "hi": "hai",
        "good": "baik",
        "bad": "buruk",
        "sorry": "maaf",
        "please": "tolong",
        "thank": "terima kasih",
        "thanks": "terima kasih",
        "welcome": "selamat datang",
        "morning": "pagi",
        "afternoon": "siang",
        "evening": "malam",
        "night": "malam",
        "day": "hari",
        "today": "hari ini",
        "tomorrow": "besok",
        "yesterday": "kemarin",
        "now": "sekarang",
        "later": "nanti",
        "soon": "segera",
        "never": "tidak pernah",
        "always": "selalu",
        "sometimes": "kadang-kadang"
    }
    
    # Konversi ke lowercase dan pisahkan kata-kata
    words = english_text.lower().replace('?', '').replace('.', '').replace(',', '').split()
    
    # Terjemahkan kata per kata
    translated_words = []
    for word in words:
        if word in translations:
            translated_words.append(translations[word])
        else:
            translated_words.append(word)  # Jika tidak ditemukan, gunakan kata asli
    
    # Gabungkan kata-kata hasil terjemahan
    translated_text = ' '.join(translated_words)
    
    # Perbaiki beberapa pola frasa khusus
    if "apa latin" in translated_text or "apa adalah latin" in translated_text:
        translated_text = translated_text.replace("apa adalah latin", "apa latin")
        translated_text = translated_text.replace("apa latin", "apa nama latin")
    
    # Tambahkan tanda tanya jika di teks asli ada tanda tanya
    if '?' in english_text:
        translated_text += '?'
    
    # Perbaiki kapitalisasi
    translated_text = translated_text.capitalize()
    
    return translated_text

def voice_chat(audio):
    """
    Fungsi utama untuk mengirimkan audio ke API dan mendapatkan respons
    """
    if audio is None:
        return None, "Silakan rekam audio terlebih dahulu", ""
    
    # Dapatkan data audio
    sr, audio_data = audio
    audio_path = None
    
    try:
        # Simpan audio ke file sementara
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
            scipy.io.wavfile.write(tmpfile.name, sr, audio_data)
            audio_path = tmpfile.name
        
        print(f"Audio disimpan di: {audio_path}")
        
        # Kirim ke API
        with open(audio_path, "rb") as f:
            files = {"file": ("voice.wav", f, "audio/wav")}
            response = requests.post(API_URL, files=files, timeout=500)
        
        print(f"Status respons API: {response.status_code}")
        
        if response.status_code == 200:
            # Simpan respons audio
            output_dir = os.path.join(tempfile.gettempdir(), "voice_chat_output")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"response_{int(time.time())}.wav")
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            # Dapatkan teks dari header base64
            transcription_b64 = response.headers.get("X-Transcription-Base64", "")
            response_text_b64 = response.headers.get("X-Response-Text-Base64", "")
            
            # Decode base64
            transcription = decode_base64(transcription_b64)
            response_text = decode_base64(response_text_b64)
            
            # Jika header base64 tidak tersedia, coba dengan header biasa (kompatibilitas mundur)
            if not transcription:
                transcription = response.headers.get("X-Transcription", "Transcription tidak tersedia")
            if not response_text:
                response_text = response.headers.get("X-Response-Text", "Response text tidak tersedia")
            
            return output_path, transcription, response_text
        else:
            error_msg = f"Error: API mengembalikan status {response.status_code}"
            try:
                error_msg += f" - {response.json().get('message', '')}"
            except:
                error_msg += f" - {response.text}"
            return None, error_msg, ""
            
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
        return None, f"Error: {str(e)}", ""
    finally:
        # Hapus file sementara
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except:
                pass

# Custom CSS untuk tampilan abu-abu dan kuning elegan dengan font Poppins
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

:root {
    --gray-dark: #333333;
    --gray-medium: #4D4D4D;
    --gray-light: #666666;
    --gray-lighter: #909090;
    --yellow-elegant: #F2D16B;
    --yellow-light: #F9E3A3;
    --yellow-dark: #D9B44A;
    --text-primary: #FFFFFF;
    --text-secondary: #E0E0E0;
    --shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    --rounded-sm: 8px;
    --rounded-md: 12px;
    --rounded-lg: 16px;
}

* {
    font-family: 'Poppins', sans-serif !important;
}

body {
    background-color: var(--gray-dark) !important;
    color: var(--text-primary) !important;
    margin: 0 !important;
    padding: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    overflow-x: hidden !important;
}

.gradio-container {
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    background-color: var(--gray-dark) !important;
}

.container-main {
    width: 100%;
    max-width: 1600px;
    margin: 0 auto;
    padding: 1.5rem;
    box-sizing: border-box;
}

.app-header {
    background-color: var(--gray-medium);
    border-radius: var(--rounded-sm);
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow);
    border-left: 5px solid var(--yellow-elegant);
}

.app-header h1 {
    margin: 0;
    color: var(--yellow-elegant);
    font-size: 1.8rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.app-subtitle {
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
    font-size: 1.1rem;
    font-weight: 300;
    letter-spacing: 0.5px;
}

.panel {
    background-color: var(--gray-medium);
    border-radius: var(--rounded-md);
    overflow: hidden;
    margin-bottom: 1rem;
    margin-left: 0.25rem;
    margin-right: 0.25rem;
    box-shadow: var(--shadow);
    height: 100%;
    border: 2px solid var(--yellow-elegant);
}

.panel-header {
    background-color: var(--gray-light);
    padding: 0.6rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.panel-header-icon {
    color: var(--yellow-elegant);
}

.panel-header-text {
    color: var(--text-primary);
    font-weight: 500;
    margin: 0;
    font-size: 0.9rem;
}

.panel-content {
    padding: 1rem;
    height: calc(100% - 3rem);
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
}

.chat-bubble {
    background-color: #464646;
    border-radius: var(--rounded-md);
    padding: 0.8rem;
    color: white !important;
    min-height: 80px;
    width: 100%;
    box-sizing: border-box;
}

.chat-bubble-user {
    background-color: #464646;
    border-left: 4px solid var(--yellow-elegant);
}

.chat-bubble-assistant {
    background-color: #464646;
    border-left: 4px solid var(--yellow-elegant);
}

/* Buttons */
.action-btn {
    border-radius: var(--rounded-md) !important;
    font-weight: 500 !important;
    padding: 0.6rem 1.2rem !important;
    border: none !important;
    transition: all 0.3s ease !important;
    box-shadow: var(--shadow) !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.5px !important;
    width: 100% !important;
    height: 45px !important;
}

.primary-btn {
    background-color: var(--yellow-elegant) !important;
    color: var(--gray-dark) !important;
}

.primary-btn:hover {
    background-color: var(--yellow-light) !important;
    transform: translateY(-2px) !important;
}

.secondary-btn {
    background-color: var(--gray-light) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--yellow-elegant) !important;
}

.secondary-btn:hover {
    background-color: var(--gray-medium) !important;
    transform: translateY(-2px) !important;
}

.button-col {
    padding: 0 0.25rem !important;
}

.status-container {
    background-color: var(--gray-medium);
    border-radius: var(--rounded-sm);
    padding: 0.6rem 0.8rem;
    border-left: 3px solid var(--yellow-elegant);
    margin: 0 0.25rem 1rem 0.25rem;
}

.status-box label {
    color: var(--yellow-elegant) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

.footer {
    text-align: center;
    margin-top: 0.75rem;
    padding: 0.75rem;
    color: var(--text-secondary);
    font-size: 0.8rem;
    border-top: 1px solid var(--gray-light);
}

/* Fix audio controls */
.audio-player {
    width: 100% !important;
}

.audio-recorder {
    width: 100% !important;
}

/* Wave visualization */
.fixed-height-container {
    min-height: 180px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Fix text displays */
.textbox-custom {
    background-color: #464646 !important;
    border-radius: 8px !important;
    color: white !important;
    border-left: 4px solid var(--yellow-elegant) !important;
    min-height: 100px !important;
    font-family: 'Poppins', sans-serif !important;
    padding: 10px !important;
    width: 100% !important;
}

.textbox-custom textarea {
    background-color: transparent !important;
    color: white !important;
    font-family: 'Poppins', sans-serif !important;
    border: none !important;
    padding: 0 !important;
    width: 100% !important;
}

/* Hide default label */
.hide-label > label {
    display: none !important;
}

/* Extra overrides */
.gradio-container, 
.gradio-container input, 
.gradio-container textarea, 
.gradio-container select {
    color: white !important;
}

/* Clear margins */
.no-margin {
    margin: 0 !important;
    padding: 0 !important;
}
"""

# Buat UI Gradio
with gr.Blocks(title="Voice Chatbot AI", css=custom_css) as demo:
    with gr.Column(elem_classes="container-main"):
        # Header
        with gr.Row(elem_classes="app-header"):
            gr.Markdown("# 🎙️ Voice Chatbot AI")
        
        gr.Markdown("### Asisten Suara Pintar Bahasa Indonesia", elem_classes="app-subtitle")
        
        # Layout utama dengan 2 kolom - Bagian Audio
        with gr.Row():
            # Kolom kiri: Input pengguna
            with gr.Column(scale=1):
                # Panel rekam pertanyaan
                with gr.Group(elem_classes="panel"):
                    with gr.Row(elem_classes="panel-header"):
                        gr.Markdown("🎤 Rekam Pertanyaan Anda", elem_classes="panel-header-text")
                    
                    with gr.Row(elem_classes="panel-content fixed-height-container"):
                        audio_input = gr.Audio(
                            sources="microphone", 
                            type="numpy",
                            elem_classes="audio-recorder",
                            label=None
                        )
            
            # Kolom kanan: Output asisten
            with gr.Column(scale=1):
                # Panel audio asisten
                with gr.Group(elem_classes="panel"):
                    with gr.Row(elem_classes="panel-header"):
                        gr.Markdown("🔊 Balasan dari Asisten", elem_classes="panel-header-text")
                    
                    with gr.Row(elem_classes="panel-content fixed-height-container"):
                        audio_output = gr.Audio(
                            type="filepath", 
                            label=None, 
                            autoplay=True,
                            elem_classes="audio-player"
                        )
        
        # Transkripsi dan Respons
        with gr.Row():
            # Transkripsi Pengguna
            with gr.Column(scale=1):
                with gr.Group(elem_classes="panel"):
                    with gr.Row(elem_classes="panel-header"):
                        gr.Markdown("💬 Teks Ucapan Anda", elem_classes="panel-header-text")
                    
                    with gr.Row(elem_classes="panel-content"):
                        transcript_display = gr.Markdown(
                            value="*Transkripsi dari pertanyaan Anda akan muncul di sini...*",
                            elem_classes="textbox-custom"
                        )
            
            # Respons Asisten
            with gr.Column(scale=1):
                with gr.Group(elem_classes="panel"):
                    with gr.Row(elem_classes="panel-header"):
                        gr.Markdown("🤖 Respons Asisten", elem_classes="panel-header-text")
                    
                    with gr.Row(elem_classes="panel-content"):
                        response_display = gr.Markdown(
                            value="*Respons asisten akan muncul di sini...*",
                            elem_classes="textbox-custom"
                        )
        
        # Status
        with gr.Row():
            with gr.Column():
                with gr.Group(elem_classes="status-container"):
                    status_box = gr.Textbox(
                        label="Status", 
                        value="Siap digunakan",
                        elem_classes="status-box"
                    )
        
        # Action buttons
        with gr.Row():
            with gr.Column(scale=1, elem_classes="button-col"):
                submit_btn = gr.Button("Proses Suara", elem_classes="action-btn primary-btn")
            with gr.Column(scale=1, elem_classes="button-col"):
                clear_btn = gr.Button("Bersihkan", elem_classes="action-btn secondary-btn")
        
        # Footer
        with gr.Row(elem_classes="footer"):
            gr.Markdown("© 2025 Voice Chatbot AI | Powered by Whisper, Gemini, & TTS")
    
    # Event handlers yang diperbarui
    def process_voice(audio):
        if audio is None:
            return None, "*Silakan rekam audio terlebih dahulu*", "*Respons asisten akan muncul di sini...*", "Silakan rekam audio terlebih dahulu"
        
        output_path, transcription, response_text = voice_chat(audio)
        
        # Tampilkan transcription dan response sebagai Markdown
        if transcription:
            # Terjemahkan transkripsi bahasa Inggris ke Indonesia
            indonesian_transcription = translate_to_indonesian(transcription)
            transcript_md = indonesian_transcription
        else:
            transcript_md = "*Tidak ada transkripsi yang tersedia*"
            
        if response_text:
            response_md = response_text
        else:
            response_md = "*Tidak ada respons yang tersedia*"
            
        return output_path, transcript_md, response_md, "Audio diproses dengan sukses"
    
    submit_btn.click(
        fn=process_voice,
        inputs=[audio_input],
        outputs=[audio_output, transcript_display, response_display, status_box]
    )
    
    # Clear handler
    def clear_all():
        return None, "*Transkripsi dari pertanyaan Anda akan muncul di sini...*", "*Respons asisten akan muncul di sini...*", "Input dan output dibersihkan"
    
    clear_btn.click(
        fn=clear_all,
        inputs=[],
        outputs=[audio_output, transcript_display, response_display, status_box]
    )
    
    # Set status when audio is recorded
    def update_status(audio):
        if audio is not None:
            return "Audio terekam, siap untuk diproses"
        return "Tidak ada audio yang terekam"
    
    audio_input.change(
        fn=update_status,
        inputs=[audio_input],
        outputs=[status_box]
    )

if __name__ == "__main__":

    output_dir = os.path.join(tempfile.gettempdir(), "voice_chat_output")
    os.makedirs(output_dir, exist_ok=True)

    demo.launch(
        server_name="127.0.0.1", 
        server_port=7860
    )
