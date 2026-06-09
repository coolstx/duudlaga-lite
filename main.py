import whisper
from pynput.keyboard import Controller, Listener, Key, KeyCode
import threading
import time
import pyaudio
import numpy as np
import tempfile
import os
import shutil
import wave

# 1. Check for FFmpeg
def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("[-] АЛДАА: FFmpeg олдсонгүй!")
        return False
    return True

if not check_ffmpeg():
    input("Гарахын тулд Enter дарна уу...")
    exit()

# 2. Load Whisper Model (Local)
print("[*] Whisper AI ачаалж байна (base)...")
model = whisper.load_model("base")

# Audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 100 # Мэдрэмжийг нэмэгдүүлэв (100-500 хооронд тохируулж болно)

audio_interface = pyaudio.PyAudio()
keyboard = Controller()
recording = False
frames = []
lock = threading.Lock()

def record_audio():
    global frames, recording
    try:
        stream = audio_interface.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        temp_frames = []
        while True:
            with lock:
                if not recording: break
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                temp_frames.append(data)
            except Exception:
                break
        stream.stop_stream()
        stream.close()
        with lock: frames = temp_frames
    except Exception as e:
        print(f"[-] Бичлэг хийхэд алдаа: {e}")

def process_and_type():
    local_frames = []
    with lock:
        local_frames = frames
        if not local_frames: return

    audio_data = b"".join(local_frames)
    audio_np_int = np.frombuffer(audio_data, dtype=np.int16)
    
    # Дууны дээд түвшинг шалгах
    max_vol = np.abs(audio_np_int).max() if len(audio_np_int) > 0 else 0

    if len(audio_np_int) == 0 or max_vol < SILENCE_THRESHOLD:
        print(f"[-] Яриа илэрсэнгүй. (Мик түвшин: {max_vol}, Босго: {SILENCE_THRESHOLD})")
        return

    print(f"[*] Whisper AI хөрвүүлж байна... (Мик түвшин: {max_vol})")
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio_interface.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(audio_data)

        # Transcribe with Whisper
        result = model.transcribe(tmp_path, fp16=False)
        raw_text = result["text"].strip()

        if raw_text:
            print(f"[+] Текст: {raw_text}")
            keyboard.type(raw_text)

        os.remove(tmp_path)
    except Exception as e:
        print(f"[-] Алдаа: {e}")
    finally:
        print("[*] Бэлэн. ('r' дарна уу)")

TRIGGER_KEY = 'r'

def on_press(key):
    global recording
    try:
        k = key.char if hasattr(key, 'char') else None
        if k == TRIGGER_KEY:
            with lock:
                if not recording:
                    recording = True
                    print("\n[*] Сонсож байна...")
                    threading.Thread(target=record_audio).start()
    except Exception:
        pass

def on_release(key):
    global recording
    try:
        k = key.char if hasattr(key, 'char') else None
        if k == TRIGGER_KEY:
            with lock:
                if recording:
                    recording = False
                    threading.Thread(target=process_and_type).start()
    except Exception:
        pass

print("=== Duudlaga Lite (Clean Version) ===")
print(f"[*] '{TRIGGER_KEY}' товчийг ДАРААД ярьж, СУЛЛАЖ дуусгана уу.")
try:
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
except KeyboardInterrupt:
    print("\n[!] Хаагдлаа.")
finally:
    audio_interface.terminate()
