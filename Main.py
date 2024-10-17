import speech_recognition as sr
import pyttsx3
import cohere
import os
import webbrowser
import pyautogui
import time
import pywhatkit as kit
import re

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


def open_website(url):
    webbrowser.open(url)
    open_websites.append(url)
    speak(f"Opened {url}.")


def close_website(url):
    if url in open_websites:
        open_websites.remove(url)
        speak(f"Closing {url}.")
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'w')
    else:
        speak(f"{url} is not currently open.")


def generate_cohere_response(command):
    prompt = f"You are a helpful assistant. Respond kindly to this question: '{command}'"
    response = cohere_client.generate(
        model='command-xlarge-nightly',
        prompt=prompt,
        max_tokens=200,
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


def execute_command(command):
    command = command.lower().strip()

    if "open google" in command:
        query = command.replace("open google", "").strip()
        if query:
            open_website(f"https://www.google.com/search?q={query}")
        else:
            open_website("https://www.google.com")

    elif "open youtube" in command:
        query = command.replace("open youtube", "").strip()
        if query:
            open_website(f"https://www.youtube.com/results?search_query={query}")
        else:
            open_website("https://www.youtube.com")

    elif "close google" in command:
        close_website("https://www.google.com")

    elif "close youtube" in command:
        close_website("https://www.youtube.com")

    elif "play" in command and "on youtube" in command:
        play_youtube(command)

    elif "open" in command:
        website = command.replace("open", "").strip()
        if website:
            website = "https://www." + website + ".com"
            open_website(website)
        else:
            speak("Please specify a website to open.")

    elif "start" in command:
        query = command.replace("start", "").strip()
        if query:
            speak(f"Starting application: {query}")
            os.system(f"start {query}")
        else:
            speak("Please specify an application to start.")

    elif "close" in command:
        website = command.replace("close", "").strip()
        if website:
            close_website(website)
        else:
            speak("Please specify a website to close.")

    elif "shutdown" in command:
        speak("Are you sure you want to shut down? Please say 'yes laptop' to confirm shut down the whole window.")
        speak("If you want to shut me down say 'yes Assistant' to confirm shut me down")
        confirmation = listen_command()
        if "yes laptop" in confirmation:
            speak("Goodbye! Shutting down now.")
            os.system("shutdown /s /t 1")
        elif "yes assistant" in confirmation:
            speak("Goodbye, shutting myself off")
            exit(0)
        else:
            speak("Shutdown cancelled.")

    elif "restart" in command:
        speak("Are you sure you want to restart? Please say 'yes' to confirm.")
        confirmation = listen_command()
        if "yes" in confirmation:
            speak("Restarting now. See you soon!")
            os.system("shutdown /r /t 1")
        else:
            speak("Restart cancelled.")

    else:
        response = generate_cohere_response(command)
        speak(response)


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
        except sr.RequestError as e:
            speak("Sorry, I couldn't reach the speech recognition service. Please check your internet connection.")
            print(f"RequestError: {e}")
            return None


def main():
    speak("Hello! I am sahira ali, your personal assistant. What can I help you with today?")
    while True:
        user_command = listen_command()
        if user_command is None:
            speak("Could you please repeat that?")
            continue
        execute_command(user_command)


if __name__ == "__main__":
    main()
