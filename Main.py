import requests  # For making HTTP requests
import json  # For parsing JSON data
import speech_recognition as sr  # For voice recognition
import pyttsx3  # For text-to-speech functionality
import cohere  # For AI text generation
import os  # For interacting with the operating system
import webbrowser
import pyautogui
import pywhatkit as kit
import re
import threading
import pvporcupine
from dotenv import load_dotenv
import playsound
import time
from pvrecorder import PvRecorder
load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
XI_API_KEY = os.getenv("ELEVENLABS_API_KEY")
PORCUPINE_API_KEY = os.getenv("PORCUPINE_API_KEY")
VOICE_ID = "cgSgspJ2msm6clMCkdW9"  
OUTPUT_PATH = "C:/Users/asus/Desktop/voice assistant/output_temp.mp3"

cohere_client = cohere.Client(COHERE_API_KEY)

recognizer = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty("voice", voices[1].id)
tts_lock = threading.Lock()
open_websites = []
wake_word_detected = False
text_limit_size = 7000 
def speak_pytts(text):
    with tts_lock:
        engine.say(text)
        engine.runAndWait()

def speak(text):
    global text_limit_size
    if text_limit_size > 0 and len(text) <= text_limit_size:
        with tts_lock:
            print(f"Siri: {text}")
            text_to_speech(text, VOICE_ID, OUTPUT_PATH)
            text_limit_size -= len(text)
            playsound.playsound(OUTPUT_PATH)
            os.remove(OUTPUT_PATH)
    else:
        print(f"Siri: {text} (using pyttsx3 due to text limit reached)")
        speak_pytts(text)

def open_website(url):
    webbrowser.open(url)
    open_websites.append(url)
    speak(f"Opened {url}.")

def close_website(url):
    if url in open_websites:
        open_websites.remove(url)
        speak(f"Closing {url}.")
        pyautogui.hotkey('ctrl', 'w')
    else:
        speak(f"{url} is not currently open.")

def generate_cohere_response(command):
    prompt = f"You are a helpful assistant. Respond kindly to this question: '{command}'"
    response = cohere_client.generate(
        model='command-xlarge-nightly',
        prompt=prompt,
        max_tokens=100,
        temperature=0.5
    )
    reply = response.generations[0].text.strip()
    return reply

# Function to play YouTube videos
def play_youtube(command):
    search_item = extract_yt_command(command)
    if search_item:
        speak(f"Playing {search_item} on YouTube")
        kit.playonyt(search_item)
    else:
        speak("Sorry, I couldn't understand the song name to play on YouTube.")

def extract_yt_command(command):
    pattern = r'play\s+(.*?)\s+on\s+youtube'
    match = re.search(pattern, command, re.IGNORECASE)
    return match.group(1) if match else None

def execute_command(command):
    command = command.lower().strip()

    if "open google" in command:
        query = command.replace("open google and search for", "").strip()
        open_website(f"https://www.google.com/search?q={query}" if query else "https://www.google.com")

    elif "open youtube" in command:
        query = command.replace("open youtube", "").strip()
        open_website(f"https://www.youtube.com/results?search_query={query}" if query else "https://www.youtube.com")

    elif "close google" in command:
        close_website("https://www.google.com")

    elif "close youtube" in command:
        close_website("https://www.youtube.com")

    elif "play" in command and "on youtube" in command:
        play_youtube(command)

    elif "open" in command:
        website = command.replace("open", "").strip()
        if website:
            open_website(f"https://www.{website}.com")
        else:
            speak("Please specify a website to open.")

    elif "start" in command:
        query = command.replace("start", "").strip()
        speak(f"Starting application: {query}")
        os.system(f"start {query}")

    elif "close" in command:
        website = command.replace("close", "").strip()
        close_website(website)

    elif "shutdown" in command:
        speak("Are you sure you want to shut down? Say 'yes assistant' to confirm.")
        confirmation = listen_command()
        if "yes assistant" in confirmation:
            speak("Goodbye, shutting down now.")
            exit(0)
        else:
            speak("Shutdown cancelled.")
    else:
        reply = generate_cohere_response(command)
        speak(reply)

def listen_command():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.1)
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"User: {command}")
            return command
        except sr.UnknownValueError:
            speak("Sorry, I did not understand that.")
            return None
        except sr.RequestError:
            speak("Sorry, I couldn't reach the speech recognition service. Please check your internet connection.")
            return None

# Detect wake word using Porcupine
def detect_wake_word():
    global wake_word_detected
    porcupine = pvporcupine.create(access_key=PORCUPINE_API_KEY, keywords=["hey siri"])
    recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
    recorder.start()

    while True:
        pcm = recorder.read()
        if porcupine.process(pcm) >= 0:
            wake_word_detected = True
            break

# Eleven Labs: Text to speech
def text_to_speech(text, voice_id, output_path):
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "Accept": "application/json",
        "xi-api-key": XI_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    response = requests.post(tts_url, headers=headers, json=data, stream=True)

    if response.ok:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
    else:
        print(response.text)

def main():
    speak("Hello! I am Siri, your personal assistant. Say the wake word once to activate.")
    detect_wake_word()

    if wake_word_detected:
        speak("Yes, I'm here. How can I help?")
        while True:
            command = listen_command()
            if command:
                execute_command(command)

if __name__ == "__main__":
    main()
