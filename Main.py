import speech_recognition as sr
import pyttsx3
import cohere
import os
import webbrowser
import pyautogui
import time
import pywhatkit as kit
import re
import threading
import pvporcupine
from pvrecorder import PvRecorder
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API keys from the environment variables
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
PORCUPINE_API_KEY = os.getenv('PORCUPINE_API_KEY')

# Initialize Cohere client with the API key from .env
cohere_client = cohere.Client(COHERE_API_KEY)

recognizer = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty("voice", voices[1].id)

tts_lock = threading.Lock()

open_websites = []
porcupine = None
recorder = None
wake_word_detected = False

def speak(text):
    with tts_lock:
        print(f"Sia: {text}")
        engine.say(text)
        engine.runAndWait()

def open_website(url):
    webbrowser.open(url)
    open_websites.append(url)
    speak(f"Opened {url}.")

def close_website(url):
    """Closes an open website."""
    if url in open_websites:
        open_websites.remove(url)
        speak(f"Closing {url}.")
        pyautogui.hotkey('ctrl', 'w')
    else:
        speak(f"{url} is not currently open.")

def generate_cohere_response(command):
    def cohere_response_async():
        prompt = f"You are a helpful assistant. Respond kindly to this question: '{command}'"
        response = cohere_client.generate(
            model='command-xlarge-nightly',
            prompt=prompt,
            max_tokens=200,
            temperature=0.5
        )
        reply = response.generations[0].text.strip()
        speak(reply)

    threading.Thread(target=cohere_response_async).start()

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
        generate_cohere_response(command)

def listen_command():
    """Listen for a command from the user."""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.1)  # Speed up noise adjustment
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"User: {command}")
            return command
        except sr.UnknownValueError:
            speak("Sorry, I did not understand that.")
            return None
        except sr.RequestError as e:
            speak("Sorry, I couldn't reach the speech recognition service. Please check your internet connection.")
            return None

def detect_wake_word():
    """Detect the wake word using Porcupine (blocking)."""
    global wake_word_detected
    porcupine = pvporcupine.create(access_key=PORCUPINE_API_KEY, keywords=["alexa"])
    recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
    recorder.start()

    while True:
        pcm = recorder.read()
        if porcupine.process(pcm) >= 0:
            wake_word_detected = True
            break

def main():
    """Main function to start the voice assistant."""
    speak("Hello! I am Sia, your personal assistant. Say the wake word once to activate.")
    detect_wake_word()

    if wake_word_detected:
        speak("Yes, I'm here. How can I help?")
        while True:
            command = listen_command()
            if command:
                execute_command(command)

if __name__ == "__main__":
    main()
