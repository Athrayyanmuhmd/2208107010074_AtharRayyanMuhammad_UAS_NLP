import os
import tempfile
import requests
import gradio as gr
import scipy.io.wavfile
import time
import shutil

def voice_chat(audio):
    if audio is None:
        return None
    
    sr, audio_data = audio
    audio_path = None
    output_audio_path = None

    try:
        # simpan sebagai .wav dengan suffix unik
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
            scipy.io.wavfile.write(tmpfile.name, sr, audio_data)
            audio_path = tmpfile.name
        
        print(f"Audio saved to temporary file: {audio_path}")
        
        # Tambahkan delay untuk memastikan file disimpan dengan benar
        time.sleep(0.5)
        
        # kirim ke endpoint FastAPI dengan timeout dan error handling
        with open(audio_path, "rb") as f:
            files = {"file": ("voice.wav", f, "audio/wav")}
            
            # Tambahkan timeout dan pengaturan lain untuk request
            response = requests.post(
                "http://localhost:8000/voice-chat", 
                files=files,
                timeout=500  
            )
        
        print(f"API response status: {response.status_code}")
        print(f"API response headers: {response.headers}")
        
        if response.status_code == 200:
            # Membuat file output dengan nama yang unik untuk menghindari konflik
            timestamp = int(time.time())
            output_dir = os.path.join(tempfile.gettempdir(), "gradio_outputs")
            os.makedirs(output_dir, exist_ok=True)
            
            output_audio_path = os.path.join(output_dir, f"response_{timestamp}.wav")
            
            # Simpan response content ke file output
            with open(output_audio_path, "wb") as f:
                f.write(response.content)
            
            print(f"Response audio saved to: {output_audio_path}")
            
            # Verifikasi file output
            if os.path.exists(output_audio_path) and os.path.getsize(output_audio_path) > 0:
                print(f"File verified: {output_audio_path}, size: {os.path.getsize(output_audio_path)} bytes")
                
                # Tambahkan delay untuk memastikan sistem file telah memperbarui informasi file
                time.sleep(0.5)
                
                return output_audio_path
            else:
                print(f"File verification failed: {output_audio_path}")
                if os.path.exists(output_audio_path):
                    print(f"File exists but size is: {os.path.getsize(output_audio_path)} bytes")
                else:
                    print("File does not exist")
                return None
        else:
            print(f"Error response: {response.text}")
            return None
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Exception occurred: {e}")
        return None
    finally:
        # Bersihkan file temporary input audio
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
                print(f"Temporary input file deleted: {audio_path}")
            except Exception as e:
                print(f"Failed to delete temporary input file: {e}")

# UI Gradio dengan pesan error yang lebih jelas
with gr.Blocks() as demo:
    gr.Markdown("# 🎙️ Voice Chatbot")
    gr.Markdown("Berbicara langsung ke mikrofon dan dapatkan jawaban suara dari asisten AI.")

    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(sources="microphone", type="numpy", label="🎤 Rekam Pertanyaan Anda")
            submit_btn = gr.Button("🔁 Submit")
        with gr.Column():
            audio_output = gr.Audio(type="filepath", label="🔊 Balasan dari Asisten")
            error_output = gr.Textbox(label="Status", placeholder="Status akan muncul di sini")

    def process_with_status(audio):
        if audio is None:
            return None, "Error: Audio input kosong. Silakan rekam suara terlebih dahulu."
        
        try:
            result = voice_chat(audio)
            if result:
                # Periksa file hasil sebelum mengembalikannya
                if os.path.exists(result) and os.path.getsize(result) > 0:
                    return result, "Success: Audio response diterima!"
                else:
                    return None, f"Error: File audio respons tidak valid. Path: {result}, Size: {os.path.getsize(result) if os.path.exists(result) else 'file tidak ada'}"
            else:
                return None, "Error: Gagal mendapatkan respons audio dari server."
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(error_details)
            return None, f"Error: {str(e)}"

    submit_btn.click(
        fn=process_with_status,
        inputs=audio_input,
        outputs=[audio_output, error_output]
    )

if __name__ == "__main__":
    # Buat folder output jika belum ada
    output_dir = os.path.join(tempfile.gettempdir(), "gradio_outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Tambahkan server_name dan server_port untuk lebih konsisten
    demo.launch(server_name="127.0.0.1", server_port=7860)