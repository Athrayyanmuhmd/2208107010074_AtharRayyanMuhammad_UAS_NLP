import os
import uuid
import tempfile
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

# path ke folder utilitas TTS
COQUI_DIR = os.path.join(BASE_DIR, "coqui_utils")

# TODO: Lengkapi jalur path ke file model TTS
# File model (misalnya checkpoint_1260000-inference.pth) harus berada di dalam folder coqui_utils/
COQUI_MODEL_PATH = os.path.join(COQUI_DIR, "checkpoint_1260000-inference.pth")

# TODO: Lengkapi jalur path ke file konfigurasi
# File config.json harus berada di dalam folder coqui_utils/
COQUI_CONFIG_PATH = os.path.join(COQUI_DIR, "config.json")

# TODO: Tentukan nama speaker yang digunakan
# Pilih nama speaker yang sesuai dengan isi file speakers.pth (misalnya: "wibowo")
COQUI_SPEAKER = "wibowo"

def transcribe_text_to_speech(text: str) -> str:
    """
    Fungsi untuk mengonversi teks menjadi suara menggunakan TTS engine yang ditentukan.
    Args:
        text (str): Teks yang akan diubah menjadi suara.
    Returns:
        str: Path ke file audio hasil konversi.
    """
    path = _tts_with_coqui(text)
    return path

# === ENGINE 1: Coqui TTS ===
def _tts_with_coqui(text: str) -> str:
    tmp_dir = tempfile.gettempdir()
    output_path = os.path.join(tmp_dir, f"tts_{uuid.uuid4()}.wav")
    
    # Dapatkan path absolut untuk semua file
    abs_model_path = os.path.abspath(COQUI_MODEL_PATH)
    abs_config_path = os.path.abspath(COQUI_CONFIG_PATH)
    abs_output_path = os.path.abspath(output_path)
    
    # Jalankan TTS dari direktori yang berisi speakers.pth
    current_dir = os.getcwd()
    
    try:
        # Pindah ke direktori coqui_utils
        os.chdir(COQUI_DIR)
        
        # jalankan Coqui TTS dengan subprocess
        cmd = [
            "tts",
            "--text", text,
            "--model_path", abs_model_path,
            "--config_path", abs_config_path,
            "--speaker_idx", COQUI_SPEAKER,
            "--out_path", abs_output_path
        ]
        
        print(f"Running TTS command from directory: {os.getcwd()}")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                print(f"TTS stdout: {result.stdout}")
            if result.stderr:
                print(f"TTS stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] TTS subprocess failed: {e}")
            if e.stdout:
                print(f"TTS stdout: {e.stdout}")
            if e.stderr:
                print(f"TTS stderr: {e.stderr}")
            return "[ERROR] Failed to synthesize speech"
            
        # Verifikasi file output
        if os.path.exists(abs_output_path):
            print(f"TTS output file created successfully: {abs_output_path}")
            return abs_output_path
        else:
            print(f"TTS output file not found at: {abs_output_path}")
            return "[ERROR] TTS output file not found"
            
    finally:
        # Kembali ke direktori asal
        os.chdir(current_dir)