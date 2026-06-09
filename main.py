import speech_recognition as sr
from pynput.keyboard import Controller, Listener, Key, KeyCode
import threading
import time

keyboard = Controller()
recognizer = sr.Recognizer()
is_recording = False

def transcribe_and_type():
    global is_recording
    if is_recording: return
    is_recording = True
    print("\n[*] Сонсож байна...")
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        text = recognizer.recognize_google(audio, language="mn-MN")
        print(f"[+] Таны яриа: {text}")
        keyboard.type(text)
    except Exception as e: print(f"[-] Алдаа: {e}")
    finally:
        is_recording = False
        print("[*] Бэлэн. (R товч дарж ярина уу)")

def on_press(key):
    try:
        if key.char == "r" or key.char == "R":
            threading.Thread(target=transcribe_and_type).start()
    except AttributeError: pass

print("=== Duudlaga Lite ===")
print("[*] R товч дараад ярьж эхэлнэ үү.")
with Listener(on_press=on_press) as listener:
    listener.join()
