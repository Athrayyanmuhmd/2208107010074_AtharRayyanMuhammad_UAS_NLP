import os
import logging
import tempfile
import shutil
import uuid
import re
import base64
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import fungsi dari modul lain
from app.stt import transcribe_speech_to_text
from app.llm import generate_response
from app.tts import transcribe_text_to_speech

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Buat instance FastAPI
app = FastAPI(title="Voice Chatbot API")

# Tambahkan CORS middleware untuk mengizinkan request dari frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mengizinkan semua origins
    allow_credentials=True,
    allow_methods=["*"],  # Mengizinkan semua methods
    allow_headers=["*"],  # Mengizinkan semua headers
    expose_headers=["X-Transcription-Base64", "X-Response-Text-Base64", "Content-Disposition", "Content-Length"],  # Expose custom headers
)

# Folder untuk menyimpan file output
OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "api_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": str(exc.detail)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": f"Terjadi kesalahan internal: {str(exc)}"},
    )

@app.get("/")
async def root():
    """Endpoint root untuk mengecek apakah API berjalan."""
    logger.info("Root endpoint diakses")
    return {"message": "Voice Chatbot API sedang berjalan. Gunakan endpoint /voice-chat untuk berinteraksi."}

# Fungsi untuk membersihkan teks header
def clean_header_value(text):
    """Membersihkan nilai untuk digunakan dalam header HTTP"""
    if text is None:
        return ""
    # Hapus karakter yang tidak valid dalam header HTTP
    # Dan batasi panjang
    clean_text = re.sub(r'[\r\n\t]', ' ', text)
    return clean_text[:200]  # Batasi panjang

# Fungsi untuk mengenkode teks ke base64
def encode_base64(text):
    """Mengenkode teks ke base64 untuk digunakan dalam header"""
    if text is None:
        return ""
    try:
        return base64.b64encode(text.encode('utf-8')).decode('ascii')
    except:
        return ""

@app.post("/voice-chat")
async def voice_chat(file: UploadFile = File(...), system_prompt: str = Form(None)):
    """
    Endpoint utama untuk interaksi voice chat.
    
    Args:
        file: File audio yang diupload dari pengguna
        system_prompt: Prompt sistem tambahan yang opsional
    
    Returns:
        FileResponse: File audio dengan respons dari chatbot
    """
    logger.info(f"Menerima permintaan voice chat dengan file: {file.filename}")
    if system_prompt:
        logger.info(f"System prompt disediakan: {system_prompt[:50]}...")
    
    temp_files = []
    try:
        # Baca konten file audio
        audio_content = await file.read()
        
        # Dapatkan ekstensi file dari nama file, defaultnya .wav jika tidak ada ekstensi
        file_ext = os.path.splitext(file.filename)[1]
        if not file_ext:
            file_ext = ".wav"  # Default extension jika tidak ada
        logger.info(f"Ekstensi file: {file_ext}")
        
        # Langkah 1: Konversi suara ke teks menggunakan Whisper
        logger.info("Memulai konversi speech-to-text")
        transcription = transcribe_speech_to_text(audio_content, file_ext)
        
        # Periksa apakah transkripsi berhasil
        if transcription.startswith("[ERROR]"):
            logger.error(f"Konversi speech-to-text gagal: {transcription}")
            raise HTTPException(status_code=500, detail=f"Konversi speech-to-text gagal: {transcription}")
        
        logger.info(f"Hasil transkripsi: {transcription}")
        
        # Langkah 2: Dapatkan respons menggunakan model Gemini
        # Tambahkan system prompt jika disediakan
        logger.info("Menghasilkan respons LLM")
        if system_prompt:
            # Catatan: ini memerlukan modifikasi pada fungsi generate_response untuk menerima system_prompt
            # Untuk saat ini, gunakan default prompt
            llm_response = generate_response(transcription)
        else:
            llm_response = generate_response(transcription)
        
        # Periksa apakah pembuatan respons berhasil
        if llm_response.startswith("[ERROR]"):
            logger.error(f"Pembuatan respons LLM gagal: {llm_response}")
            raise HTTPException(status_code=500, detail=f"Pembuatan respons LLM gagal: {llm_response}")
        
        logger.info(f"Respons LLM: {llm_response}")
        
        # Langkah 3: Konversi teks respons menjadi suara
        logger.info("Mengkonversi teks ke suara")
        audio_response_path = transcribe_text_to_speech(llm_response)
        
        # Periksa apakah path respons audio valid
        if isinstance(audio_response_path, str) and audio_response_path.startswith("[ERROR]"):
            logger.error(f"Konversi text-to-speech gagal: {audio_response_path}")
            raise HTTPException(status_code=500, detail=f"Konversi text-to-speech gagal: {audio_response_path}")
        
        # Verifikasi file response
        if not os.path.exists(audio_response_path):
            logger.error(f"Audio response file not found: {audio_response_path}")
            raise HTTPException(status_code=500, detail="Audio response file not found")
        
        file_size = os.path.getsize(audio_response_path)
        if file_size == 0:
            logger.error(f"Audio response file is empty: {audio_response_path}")
            raise HTTPException(status_code=500, detail="Audio response file is empty")
        
        logger.info(f"Respons audio diverifikasi - path: {audio_response_path}, size: {file_size} bytes")
        
        # Salin file ke lokasi permanen dalam OUTPUT_DIR dengan nama yang unik
        # untuk memastikan file tidak terhapus oleh sistem pembersihan tmp
        permanent_filename = f"response_{uuid.uuid4()}.wav"
        permanent_path = os.path.join(OUTPUT_DIR, permanent_filename)
        
        # Salin file dengan shutil
        shutil.copy2(audio_response_path, permanent_path)
        temp_files.append(permanent_path) # Tambahkan ke daftar file temporary
        
        logger.info(f"File audio response disalin ke path permanen: {permanent_path}")
        
        # Periksa kembali file yang baru disalin
        if not os.path.exists(permanent_path):
            logger.error(f"Permanent audio file not found after copy: {permanent_path}")
            raise HTTPException(status_code=500, detail="Failed to create permanent audio file")
        
        perm_file_size = os.path.getsize(permanent_path)
        logger.info(f"Permanent file verified - path: {permanent_path}, size: {perm_file_size} bytes")
        
        # Langkah 4: Kembalikan file audio dengan header yang tepat
        # Gunakan base64 encoding untuk menghindari masalah karakter invalid dalam header
        logger.info("Mengembalikan respons audio ke klien")
        
        # Enkode teks ke base64 untuk menghindari masalah dengan karakter tidak valid
        transcription_b64 = encode_base64(transcription)
        response_text_b64 = encode_base64(llm_response)
        
        headers = {
            "Content-Disposition": f"attachment; filename=response.wav",
            "Content-Length": str(perm_file_size),
            "Access-Control-Expose-Headers": "X-Transcription-Base64, X-Response-Text-Base64, Content-Disposition, Content-Length",
            "X-Transcription-Base64": transcription_b64,
            "X-Response-Text-Base64": response_text_b64
        }
        
        return FileResponse(
            path=permanent_path,
            media_type="audio/wav",
            filename="response.wav",
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat memproses permintaan voice chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")

# Untuk menjalankan aplikasi dengan uvicorn
if __name__ == "__main__":
    import uvicorn
    logger.info("Memulai Voice Chatbot API")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
