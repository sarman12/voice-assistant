

import speech_recognition as sr
import pyttsx3
import subprocess
import os
import webbrowser
import wikipedia
import asyncio
import cohere
import random

# Initialize Cohere client
cohere_client = cohere.Client("XLK2VqK7ocr7Xv3I3ZeHlCN1N335jSoCaiAdYKkS")  # Replace with your actual API key

# Initialize recognizer and text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Set voice to female (if available)
voices = engine.getProperty('voices')
female_voice_found = False
for voice in voices:
    if "female" in voice.name.lower() or "woman" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        female_voice_found = True
        print(f"Female voice set: {voice.name}")
        break

if not female_voice_found:
    print("Female voice not found. Using default voice.")
    engine.setProperty('voice', voices[0].id) 
    
predefined_responses = {
    "open google": ["Opening Google for you!", "Sure! Let me open Google.", "Got it! Opening Google now."],
    "open media player": ["Opening Media Player. Enjoy your music!", "Media Player is on the way!", "Let’s play some tunes!"],
    "volume up": ["Turning up the volume!", "Sure, I’ll make it louder.", "Boosting the volume now!"],
    "volume down": ["Turning down the volume.", "Okay, reducing the volume.", "Lowering the volume for you."],
    "shutdown": ["Goodbye! Shutting down now.", "See you later! I'm going offline.", "Shutting down. Take care!"],
    "goodbye": ["Goodbye! Have a great day!", "See you next time!", "Take care! Goodbye!"],
    "exit": ["Exiting now. Bye!", "Alright, I'm off. Goodbye!", "Closing down. See you!"]
}

# Make the assistant speak and print the text
def speak(text):
    print(f"Sia: {text}")  # Print the text that Sia is saying
    engine.say(text)
    engine.runAndWait()

# Listen to user commands with confidence check
def listen_command():
    try:
        with sr.Microphone() as source:
            print("Listening for commands...")

            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source)

            # Initialize an empty string to hold the final command
            full_command = ""

            # Keep listening until silence is detected
            while True:
                audio = recognizer.listen(source, timeout=5)  # Adjust timeout as necessary

                try:
                    # Recognize speech using Google Web Speech API
                    response = recognizer.recognize_google(audio)
                    full_command += " " + response.lower()  # Append recognized text
                    print(f"Recognized so far: {full_command.strip()}")

                except sr.UnknownValueError:
                    # If speech is unintelligible, continue listening
                    continue
                except sr.RequestError:
                    # Handle network issues
                    speak("Sorry, I'm having trouble with the network.")
                    return ""

                # Check if there's a pause in speech for a short duration
                if len(full_command.split()) > 0 and audio.energy_threshold < 300:  # Adjust the threshold as necessary
                    break

            return full_command.strip()  # Return the full command

    except sr.RequestError:
        speak("Sorry, I'm having trouble with the network.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return ""


# Improved Wikipedia search handling
def search_wikipedia(query):
    try:
        result = wikipedia.summary(query, sentences=2)
        return result
    except wikipedia.exceptions.DisambiguationError:
        return "Your query is too ambiguous, please be more specific."
    except wikipedia.exceptions.PageError:
        return "I couldn't find any results on Wikipedia."

# Generate Cohere response
def generate_cohere_response(prompt):
    response = cohere_client.generate(
        model='command-r-plus-08-2024',  # Ensure you are using the correct model
        prompt=prompt,
        max_tokens=100,  # Adjust as needed
        temperature=0.9  # Adjust creativity level
    )
    return response.generations[0].text.strip()  # Return the generated text

# Basic intent recognition
def recognize_intent(command):
    for key in predefined_responses:
        if key in command:
            return key
    return None  # No recognized intent

# Handle commands and add new features
async def execute_command(command):
    intent = recognize_intent(command)
    
    if intent:
        response_variants = predefined_responses[intent]
        response = random.choice(response_variants)  # Select a random response variant
        speak(response)
        if intent in ["shutdown", "goodbye", "exit"]:
            os._exit(0)  # Force exit to terminate all threads
    elif 'search wikipedia for' in command:
        query = command.replace("search wikipedia for", "").strip()
        result = search_wikipedia(query)
        speak(f"According to Wikipedia, {result}")
    elif 'what is' in command or 'who is' in command:
        result = search_wikipedia(command)
        speak(result)
    elif 'search the web for' in command:
        query = command.replace("search the web for", "").strip()
        speak(f"Searching the web for {query}.")
        webbrowser.open(f"https://www.google.com/search?q={query}")
    else:
        # Cohere for open-ended questions or other commands
        speak("Let me think for a moment...")
        response = generate_cohere_response(command)
        print(f"Sia's Cohere response: {response}")
        speak(response)

# Main loop with sequential command processing
async def main():
    # Introduction by Sia
    speak("Hello! I am Sia, your personal assistant, created by Sahanee. What can I help you with today?")

    while True:
        user_command = listen_command()
        if user_command:
            await execute_command(user_command)

# Run the assistant
if __name__ == "__main__":
    asyncio.run(main())
