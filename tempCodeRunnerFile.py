import requests
import json 
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
import playsound
import time
from pvrecorder import PvRecorder
from newsapi import NewsApiClient
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager


load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
XI_API_KEY = os.getenv("ELEVENLABS_API_KEY")
PORCUPINE_API_KEY = os.getenv("PORCUPINE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
VOICE_ID = "cgSgspJ2msm6clMCkdW9"  
OUTPUT_PATH = "C:/Users/asus/Desktop/voice assistant/output_temp.mp3"


newsapi = NewsApiClient(api_key=NEWS_API_KEY)


cohere_client = cohere.Client(COHERE_API_KEY)

recognizer = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty("voice", voices[1].id)
tts_lock = threading.Lock()
open_websites = []
wake_word_detected = False
text_limit_size = 7000 

# Initialize Selenium WebDriver for Edge
def initialize_driver():
    edge_service = EdgeService(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=edge_service)
    return driver

from selenium.webdriver.common.by import By

# Play song on YouTube Music
def play_yt_music(song_name):
    try:
        driver = initialize_driver()
        driver.get("https://music.youtube.com")
        time.sleep(3)  # Give the page time to load

        # Accept cookies or close any pop-ups if present
        try:
            consent_button = driver.find_element(By.XPATH, "//button[contains(text(), 'I agree')]")
            consent_button.click()
        except Exception as e:
            print("No consent button found. Continuing...")

        # Locate the search bar and input the song name
        search_box = driver.find_element(By.NAME, "search_query")
        search_box.send_keys(song_name)
        search_box.send_keys(Keys.RETURN)
        
        time.sleep(3)  # Wait for search results to load

        # Click on the first search result
        first_result = driver.find_element(By.XPATH, "(//ytmusic-responsive-list-item-renderer)[1]")
        first_result.click()

        speak(f"Playing {song_name} on YouTube Music.")
    except Exception as e:
        speak(f"Sorry, I couldn't play {song_name} on YouTube Music due to an error.")
        print(f"Error: {str(e)}")




def speak_pytts(text):
    with tts_lock:
        engine.say(text)
        engine.runAndWait()
        

def calculate(expression):
    try:
        result = eval(expression)
        return f"The result is {result}"
    except Exception as e:
        return "I couldn't calculate that."


def extract_time(command):
    pattern = r"(?:(\d+)\s*minutes?)?\s*(?:and\s*)?(?:(\d+)\s*seconds?)?"
    
    match = re.search(pattern, command)
    if match:
        minutes = int(match.group(1)) if match.group(1) else 0
        seconds = int(match.group(2)) if match.group(2) else 0
        total_seconds = minutes * 60 + seconds
        return total_seconds
    else:
        return None


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


def set_timer(duration_in_seconds):
    speak(f"Setting a timer for {duration_in_seconds // 60} minutes and {duration_in_seconds % 60} seconds.")
    time.sleep(duration_in_seconds)
    speak("Time's up!")

def speak(text):
    # global text_limit_size
    # if text_limit_size > 0 and len(text) <= text_limit_size:
    #     with tts_lock:
    #         print(f"Siri: {text}")
    #         text_to_speech(text, VOICE_ID, OUTPUT_PATH)
    #         text_limit_size -= len(text)
    #         playsound.playsound(OUTPUT_PATH)
    #         os.remove(OUTPUT_PATH)
    # else:
    #     print(f"Siri: {text} (using pyttsx3 due to text limit reached)")
        speak_pytts(text)

def open_website(url):
    webbrowser.open(url)
    open_websites.append(url)
    speak(f"Opened {url}.")
    
    
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

def execute_command(command):
    command = command.lower().strip()
    
    if "tell me a joke" in command:
        tell_joke()
    elif "open google" in command:
        query = command.replace("open google and search for", "").strip()
        open_website(f"https://www.google.com/search?q={query}" if query else "https://www.google.com")

    elif "open youtube" in command:
        query = command.replace("open youtube", "").strip()
        open_website(f"https://www.youtube.com/results?search_query={query}" if query else "https://www.youtube.com")

    elif "close google" in command:
        close_website("https://www.google.com")

    elif "close youtube" in command:
        close_website("https://www.youtube.com")

    elif "play" in command and "on youtube music" in command:
        song_name = re.search(r'play\s+(.*?)\s+on\s+youtube music', command, re.IGNORECASE)
        if song_name:
            song_name = song_name.group(1)
            play_yt_music(song_name)
        else:
            speak("Sorry, I couldn't understand the song name to play on YouTube Music.")
            
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
        
    elif "calculate" in command:
        expression = command.replace("calculate", "").strip()
        result = calculate(expression)
        speak(result)

    elif "close" in command:
        website = command.replace("close", "").strip()
        close_website(website)
        
    elif "set a timer" in command:
        duration = extract_time(command)
        set_timer(duration)

    elif "shutdown" in command:
        speak("Are you sure you want to shut down? Say 'yes assistant' to confirm.")
        confirmation = listen_command()
        if "yes assistant" in confirmation:
            speak("Goodbye, shutting down now.")
            exit(0)
        else:
            speak("Shutdown cancelled.")
            
    elif "news" in command and "headlines" in command:
        speak("Which category would you like news from? For example, business, technology, sports, entertainment, or health.")
        category = listen_command()
        if category:
            speak(f"Fetching news for the {category} category.")
            headlines = news(category)
            speak(headlines)
        else:
            speak("Sorry, I didn't catch that. Please try again.")
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