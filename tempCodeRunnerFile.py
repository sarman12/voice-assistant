import speech_recognition as sr
import pyttsx3
import subprocess
import os
import webbrowser
import asyncio
import cohere
import random
import requests
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Initialize Cohere client
cohere_client = cohere.Client("XLK2VqK7ocr7Xv3I3ZeHlCN1N335jSoCaiAdYKkS")

recognizer = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
female_voice_found = False

for voice in voices:
    if "female" in voice.name.lower() or "woman" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        female_voice_found = True
        break

if not female_voice_found:
    engine.setProperty("voice", voices[0].id) 

predefined_responses = {
    "open google": ["Opening Google for you!", "Sure! Let me open Google.", "Got it! Opening Google now."],
    "open youtube": ["Opening YouTube now!", "Let me get YouTube for you.", "Opening YouTube! Enjoy!"],
    "shutdown": ["Goodbye! Shutting down now.", "See you later! I'm going offline.", "Shutting down. Take care!"],
    "restart": ["Restarting now. See you soon!", "Hold on! Restarting your computer.", "Restarting the system."],
    "play music": ["Opening Jio Saavn for music!", "Let’s play some music on Jio Saavn!", "Playing music for you!"],
    "how are you": ["I'm doing great, thank you!", "I'm fine! How can I help you today?", "Feeling ready to assist you!"],
    "tell me a joke": ["Why don't scientists trust atoms? Because they make up everything!", "What did the ocean say to the shore? Nothing, it just waved!", "Why don’t skeletons fight each other? They don’t have the guts."]
}

# Initialize Spotify API
# sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="YOUR_SPOTIFY_CLIENT_ID",
#                                                client_secret="YOUR_SPOTIFY_CLIENT_SECRET",
#                                                redirect_uri="YOUR_SPOTIFY_REDIRECT_URI",
#                                                scope="user-read-playback-state,user-modify-playback-state"))

# Function to speak text
def speak(text):
    print(f"Sia: {text}")
    engine.say(text)
    engine.runAndWait()

def listen_command():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            speak("I'm listening...")
            full_command = ""
            while True:
                audio = recognizer.listen(source, timeout=5)
                try:
                    response = recognizer.recognize_google(audio)
                    full_command += " " + response.lower()
                    print(f"Recognized so far: {full_command.strip()}")
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    speak("Sorry, I'm having trouble with the network.")
                    return ""
                if len(full_command.split()) > 0:
                    break
            return full_command.strip()
    except Exception as e:
        print(f"An error occurred: {e}")
    return ""

def generate_cohere_response(prompt):
    try:
        response = cohere_client.generate(
            model='command-xlarge-nightly',
            prompt=prompt,
            max_tokens=600,
            temperature=0.7
        )
        return response.generations[0].text.strip()
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I couldn't come up with a good response right now."

def get_weather(city):
    base_url = f"https://api.openweathermap.org/data/2.5/weather?units=metric&q={city}&appid=65f7b612e3b7902c807bca207f229519"
    try:
        response = requests.get(base_url)
        data = response.json()
        if data["cod"] != "404":
            weather_data = data["main"]
            temperature = weather_data["temp"]
            weather_desc = data["weather"][0]["description"]
            return f"The current temperature in {city} is {temperature}°C with {weather_desc}."
        else:
            return "City not found. Please check the name and try again."
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return "I'm having trouble fetching the weather right now."

# Function to fetch news headlines
def get_latest_news():
    api_key = "44fd80cf5de5452baa77aa33c106fc0b"
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
    try:
        response = requests.get(url)
        articles = response.json().get('articles')
        headlines = [f"{article['title']}" for article in articles[:10]]  # First 5 headlines
        return "Here are the latest news headlines:\n" + "\n".join(headlines)
    except Exception as e:
        print(f"Error fetching news: {e}")
        return "Sorry, I can't fetch the news right now."

# Function to fetch unread emails
def get_unread_emails():
    creds = Credentials.from_authorized_user_file('token.json')
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
        messages = results.get('messages', [])
        if not messages:
            return "You have no unread emails."
        else:
            emails = []
            for msg in messages[:5]:
                msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
                snippet = msg_data['snippet']
                emails.append(snippet)
            return "\n".join(emails)
    except Exception as e:
        print(f"Error retrieving emails: {e}")
        return "Unable to retrieve emails right now."

# Timer function
def set_timer(minutes):
    speak(f"Setting a timer for {minutes} minutes.")
    time.sleep(minutes * 60)  # Convert minutes to seconds
    speak("Time's up!")

# Reminder function
def set_reminder(task, minutes):
    speak(f"I will remind you to {task} in {minutes} minutes.")
    time.sleep(minutes * 60)
    speak(f"Reminder: It's time to {task}.")

# Spotify song playback
# def play_on_spotify(song):
#     try:
#         results = sp.search(q=song, limit=1)
#         track = results['tracks']['items'][0]['uri']
#         sp.start_playback(uris=[track])
#         speak(f"Playing {song} on Spotify.")
#     except Exception as e:
#         print(f"Error with Spotify: {e}")
#         speak("Sorry, I couldn't play that song right now.")

# Command execution logic
async def execute_command(command):
    if "open google" in command:
        response = random.choice(predefined_responses["open google"])
        speak(response)
        webbrowser.open("https://www.google.com")

    elif "open youtube" in command:
        video_title = command.replace("open youtube", "").strip()
        response = random.choice(predefined_responses["open youtube"])
        speak(response)
        if video_title:
            webbrowser.open(f"https://www.youtube.com/results?search_query={video_title}")
        else:
            webbrowser.open("https://www.youtube.com")

    elif "weather in " in command:
        city = command.replace("weather", "").strip()
        if city:
            weather_info = get_weather(city)
            speak(weather_info)
        else:
            speak("Please provide the city name.")

    elif "news" in command:
        news = get_latest_news()
        speak(news)

    elif "email" in command:
        email_snippets = get_unread_emails()
        speak(email_snippets)

    elif "set timer" in command:
        minutes = int(command.replace("set timer", "").strip())
        set_timer(minutes)

    elif "remind me" in command:
        task = command.replace("remind me", "").split("in")[0].strip()
        minutes = int(command.split("in")[-1].strip().split()[0])
        set_reminder(task, minutes)

    # elif "play on spotify" in command:
    #     song = command.replace("play on spotify", "").strip()
    #     play_on_spotify(song)

    elif "how are you" in command:
        response = random.choice(predefined_responses["how are you"])
        speak(response)

    elif "tell me a joke" in command:
        response = random.choice(predefined_responses["tell me a joke"])
        speak(response)

    elif "shutdown" in command:
        response = random.choice(predefined_responses["shutdown"])
        speak(response)
        os.system("shutdown /s /t 1")

    elif "restart" in command:
        response = random.choice(predefined_responses["restart"])
        speak(response)
        os.system("shutdown /r /t 1")

    else:
        speak("Let me think for a moment...")
        response = generate_cohere_response(command)
        speak(response)

# Main function
async def main():
    speak("Hello! I am Sia, your personal assistant, created by Sahanee. What can I help you with today?")
    while True:
        user_command = listen_command()
        if user_command:
            await execute_command(user_command)

# Run the main event loop
if __name__ == "__main__":
    asyncio.run(main())
