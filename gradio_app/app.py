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

# Buat UI Gradio
with gr.Blocks(title="Voice Chatbot") as demo:
    gr.Markdown("# 🎙️ Voice Chatbot")
    gr.Markdown("Rekam pertanyaan Anda dan dapatkan respons suara dari asisten AI")
    
    with gr.Row():
        # Panel input
        with gr.Column():
            gr.Markdown("### Input Suara")
            audio_input = gr.Audio(
                sources="microphone", 
                type="numpy", 
                label="Rekam Pertanyaan"
            )
            submit_btn = gr.Button("Proses", variant="primary")
            clear_btn = gr.Button("Bersihkan", variant="secondary")
        
        # Panel output
        with gr.Column():
            gr.Markdown("### Respons Asisten")
            audio_output = gr.Audio(type="filepath", label="Respons Suara", autoplay=True)
            transcript_box = gr.Textbox(label="Input Anda (Speech-to-Text)", lines=3)
            response_box = gr.Textbox(label="Respons AI", lines=3)
            status_box = gr.Textbox(label="Status", value="Siap digunakan")
    
    gr.Markdown("### Petunjuk Penggunaan")
    gr.Markdown("""
    1. Klik tombol mikrofon untuk mulai merekam
    2. Bicarakan pertanyaan atau instruksi Anda
    3. Klik tombol stop untuk mengakhiri rekaman
    4. Klik tombol "Proses" untuk mengirim audio
    5. Tunggu beberapa saat untuk mendapatkan respons
    """)
    
    # Event handlers
    submit_btn.click(
        fn=voice_chat,
        inputs=[audio_input],
        outputs=[audio_output, transcript_box, response_box]
    )
    
    # Clear handler
    def clear_outputs():
        return None, "", "", "Input dan output dibersihkan"
    
    clear_btn.click(
        fn=clear_outputs,
        inputs=[],
        outputs=[audio_output, transcript_box, response_box, status_box]
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
    # Buat folder output jika belum ada
    output_dir = os.path.join(tempfile.gettempdir(), "voice_chat_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Jalankan aplikasi
    demo.launch(server_name="127.0.0.1", server_port=7860)
