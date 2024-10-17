import speech_recognition as sr
import pyttsx3
import cohere
import asyncio
import os
import webbrowser
import pyautogui
import time

cohere_client = cohere.Client("XLK2VqK7ocr7Xv3I3ZeHlCN1N335jSoCaiAdYKkS")
recognizer = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty("voice", voices[1].id)

open_websites = []

def speak(text):
    print(f"Sia: {text}")
    engine.say(text)
    engine.runAndWait()

def open_and_navigate_website(url):
    webbrowser.open(url)
    open_websites.append(url)
    speak(f"Opened {url}.")

def close_website(url):
    if url in open_websites:
        open_websites.remove(url)
        speak(f"Closing {url}.")
        time.sleep(1)  # Give a second for the browser to be ready
        pyautogui.hotkey('ctrl', 'w')  # Close the current tab
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
    return response.generations[0].text.strip()

async def execute_command(command):
    command = command.lower().strip()
    
    if "open google" in command:
        query = command.replace("open google", "").strip()
        if query:
            open_and_navigate_website(f"https://www.google.com/search?q={query}")
        else:
            open_and_navigate_website("https://www.google.com")

    elif "open youtube" in command:
        query = command.replace("open youtube", "").strip()
        if query:
            open_and_navigate_website(f"https://www.youtube.com/results?search_query={query}")
        else:
            open_and_navigate_website("https://www.youtube.com")

    elif "close google" in command:
        close_website("https://www.google.com")

    elif "close youtube" in command:
        close_website("https://www.youtube.com")

    elif "open" in command:
        website = command.replace("open", "").strip()
        if website:
            website = "https://www." + website + ".com"
            open_and_navigate_website(website)
        else:
            speak("Please specify a website to open.")

    elif "close" in command:
        website = command.replace("close", "").strip()
        if website:
            close_website(website)
        else:
            speak("Please specify a website to close.")

    elif "shutdown" in command:
        speak("Goodbye! Shutting down now.")
        os.system("shutdown /s /t 1")

    elif "restart" in command:
        speak("Restarting now. See you soon!")
        os.system("shutdown /r /t 1")

    else:
        response = generate_cohere_response(command)
        speak(response)

def listen_command():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"User: {command}")
            return command
        except sr.UnknownValueError:
            speak("Sorry, I did not understand that.")
            return None
        except sr.RequestError:
            speak("Could not request results from Google Speech Recognition service.")
            return None

async def main():
    speak("Hello! I am Sia, your personal assistant. What can I help you with today?")
    while True:
        user_command = listen_command()
        if user_command:
            await execute_command(user_command)

if __name__ == "__main__":
    asyncio.run(main())
