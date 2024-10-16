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
import threading

# Initialize Cohere client
cohere_client = cohere.Client("XLK2VqK7ocr7Xv3I3ZeHlCN1N335jSoCaiAdYKkS")

recognizer = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
female_voice_found = False
stop_talking = False
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

# Function to handle stop button functionality
def stop_button_listener():
    global stop_talking
    while True:
        input("Press Enter to stop talking and start listening again...")  # Simulate a stop button
        stop_talking = True

# Function to speak text
def speak(text):
    global stop_talking
    print(f"Sia: {text}")
    engine.say(text)
    engine.runAndWait()

    # If stop_talking flag is triggered, stop the speech and start listening
    if stop_talking:
        engine.stop()
        stop_talking = False  # Reset the flag

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

# Other functions remain the same (omitted for brevity)

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

    # Other command executions are the same (omitted for brevity)

# Main function
async def main():
    speak("Hello! I am Sia, your personal assistant, created by Sahanee. What can I help you with today?")
    
    # Start the stop button listener in a separate thread
    stop_button_thread = threading.Thread(target=stop_button_listener)
    stop_button_thread.daemon = True
    stop_button_thread.start()
    
    while True:
        user_command = listen_command()
        if user_command:
            await execute_command(user_command)

# Run the main event loop
if __name__ == "__main__":
    asyncio.run(main())

