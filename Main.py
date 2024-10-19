import requests
import speech_recognition as sr
import pyttsx3
import cohere
import os
import webbrowser
import pyautogui
import pywhatkit as kit
import re
import threading
import pvporcupine
from dotenv import load_dotenv
import time
from pvrecorder import PvRecorder
from newsapi import NewsApiClient
import io
from pydub import AudioSegment
from pydub.playback import play
from threading import Event

load_dotenv()
recognizer = sr.Recognizer()
open_websites = []
wake_word_detected = False
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty("voice", voices[1].id)
tts_lock = threading.Lock()

def speak_pytts(text):
    with tts_lock:
        engine.say(text)
        engine.runAndWait()

VOICE_ID = "cgSgspJ2msm6clMCkdW9"
XI_API_KEY = os.getenv("ELEVENLABS_API_KEY")
speak_done_event = Event()
text_limit_size = 6000

def text_to_speech(text, voice_id):
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
        audio_data = io.BytesIO()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                audio_data.write(chunk)
        audio_data.seek(0)
        audio = AudioSegment.from_file(audio_data, format="mp3")
        play(audio)
        speak_done_event.set()
    else:
        print("Error:", response.text)

def speak(text):
    global XI_API_KEY
    if text_limit_size > 0:
        with tts_lock:
            print(f"Siri: {text}")
            speak_done_event.clear()
            tts_thread = threading.Thread(target=text_to_speech, args=(text, VOICE_ID))
            tts_thread.start()
            speak_done_event.wait()
    else:
        print(f"Siri: {text} (using pyttsx3 due to text limit reached)")
        speak_pytts(text)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

def SpecificNews(text):
    try:
        specific_news_url = f"https://newsapi.org/v2/everything?q={text}&apiKey={NEWS_API_KEY}"
        response = requests.get(specific_news_url)
        news_data = response.json()
        articles = news_data.get('articles', [])
        
        if articles:
            top_articles = articles[:10]
            news = [i['title'] for i in top_articles]
            return f"Here are the top 10 news about {text}: " + ", ".join(news)
        else:
            return f"Sorry, I couldn't find any news about {text}."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def news(category):
    try:
        top_headlines = newsapi.get_top_headlines(
            category=category,
            language='en',
            country='us'
        )
        articles = top_headlines['articles']
        if articles:
            headlines = [article['title'] for article in articles]
            return "Here are the top headlines in " + category + ": " + ", ".join(headlines)
        else:
            return f"Sorry, I couldn't find any news in the {category} category."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def extract_time(command):
    pattern = r"(\d+)\s*(?:minutes?|mins?)?\s*(?:(?:and\s*)?(\d+)\s*(?:seconds?|secs?)?)?"
    match = re.search(pattern, command)
    if match:
        minutes = int(match.group(1)) if match.group(1) else 0
        seconds = int(match.group(2)) if match.group(2) else 0
        return minutes * 60 + seconds
    else:
        return None

def set_timer(duration_in_seconds):
    speak(f"Setting a timer for {duration_in_seconds // 60} minutes and {duration_in_seconds % 60} seconds.")
    time.sleep(duration_in_seconds)
    speak("Time's up!")

def tell_joke():
    response = requests.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"})
    if response.status_code == 200:
        joke = response.json()['joke']
        speak(joke)
    else:
        speak("Sorry, I couldn't fetch a joke right now.")

def close_website(url):
    if url in open_websites:
        open_websites.remove(url)
        speak(f"Closing {url}.")
        pyautogui.hotkey('ctrl', 'w')
    else:
        speak(f"{url} is not currently open.")

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
cohere_client = cohere.Client(COHERE_API_KEY)

def generate_cohere_response(command):
    prompt = f"You are a helpful assistant. Respond kindly to this question: '{command}'"
    response = cohere_client.generate(
        model='command-xlarge-nightly',
        prompt=prompt,
        max_tokens=100,
        temperature=0.5
    )
    return response.generations[0].text.strip()

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

def open_website(url):
    webbrowser.open(url)
    open_websites.append(url)
    speak(f"Opened {url}.")

def open_web(command):
    query = command.replace("open", "").strip()

    if "google and search for" in query:
        search_query = query.split("google and search for", 1)[1].strip()
        website = f"https://www.google.com/search?q={search_query}"
        open_website(website)
    elif "youtube and search for" in query:
        search_query = query.split("youtube and search for", 1)[1].strip()
        website = f"https://www.youtube.com/results?search_query={search_query}"
        open_website(website)
    else:
        open_website(f"https://www.{query}.com")

def confirm_shutdown():
    speak("Are you sure you want to shut me down? Say 'deactivate' to confirm.")
    confirmation = listen_command()

    if confirmation and "deactivate" in confirmation.lower():
        speak("Goodbye, shutting down now.")
        exit(0)

def execute_command(command):
    global wake_word_detected
    command = command.lower().strip()
    
    if "open" in command:
        open_web(command)
    elif "tell me a joke" in command:
        tell_joke()
    elif "close google" in command:
        close_website("https://www.google.com")
    elif "close youtube" in command:
        close_website("https://www.youtube.com")
    elif "start" in command:
        query = command.replace("start", "").strip()
        speak(f"Starting application: {query}")
        os.system(f"start {query}")
    elif "close" in command:
        website = command.replace("close", "").strip()
        close_website(website)
    elif "play" in command and "on youtube" in command:
        play_youtube(command)
    elif "set a timer" in command:
        duration = extract_time(command)
        if duration:
            set_timer(duration)
        else:
            speak("I didn't catch the time. Please specify in minutes and seconds.")
    elif "shutdown assistant" in command:
        confirm_shutdown()
    elif "shutdown the computer" in command:
        speak("Are you sure you want to shut down the computer? Say 'ok' to confirm.")
        confirmation = listen_command()
        if confirmation and "ok" in confirmation:
            speak("Goodbye, shutting down the computer.")
            os.system("shutdown /s /t 5")
        else:
            speak("Shutdown cancelled.")
    elif "news" in command and "headlines" in command:
        speak("Which category would you like news from? For example, business, technology, sports, entertainment, or health.")
        category = listen_command()
        if category:
            speak(f"Fetching news for the {category} category.")
            headlines = news(category)
            speak(headlines)
    elif "news" in command and "about" in command:
        query = command.replace("news", "").replace("about", "").strip()
        speak(f"Fetching news about {query}.")
        reply = SpecificNews(query)
        speak(reply)
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
            speak("Sorry, I didn't catch that. Can you please repeat?")
            return None
        except sr.RequestError:
            speak("Sorry, I couldn't reach the speech recognition service. Please check your internet connection.")
            return None

        
PORCUPINE_API_KEY = os.getenv("PORCUPINE_API_KEY")
def detect_wake_word():
    global wake_word_detected
    porcupine = pvporcupine.create(access_key=PORCUPINE_API_KEY, keywords=["hey siri"])
    recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
    recorder.start()

    while True:
        pcm = recorder.read()
        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            wake_word_detected = True
            break

def main():
    speak("Hello! I am Siri, your personal assistant. Say the wake word once to activate.")
    detect_wake_word()
    if wake_word_detected:
        speak("Yes, I'm here. How can I help?")
        while True:
            if not processing_command:
                command = listen_command()
                if command:
                    processing_command = True
                    execute_command(command)
                    processing_command = False




if __name__ == "__main__":
    main()
