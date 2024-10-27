Siri - Voice Assistant
Siri is a personal voice-controlled assistant built using Python. It listens for voice commands after detecting a wake word ("Hey Siri") and performs tasks such as playing YouTube videos, opening websites, telling jokes, fetching news, and more.

Features
Voice Command Recognition: Triggered by the wake word "Hey Siri".
Text-to-Speech (TTS): Uses ElevenLabs for natural-sounding voice responses, with pyttsx3 as a fallback.
Task Automation:
Play YouTube videos
Open and close websites
Fetch news from specific categories or topics
Tell jokes
Set timers
Shutdown commands for assistant or computer
Requirements
Python 3.x
Libraries:
requests
speech_recognition
pyttsx3
cohere
pydub
porcupine
newsapi-python
pywhatkit
pyautogui
dotenv
Installation
Clone the repository:

bash
Copy code
git clone https://github.com/your-username/siri-voice-assistant.git
cd siri-voice-assistant
Install the required dependencies:

bash
Copy code
pip install -r requirements.txt
Set up the environment variables:

ELEVENLABS_API_KEY: For text-to-speech functionality.
NEWS_API_KEY: For fetching news.
PORCUPINE_API_KEY: For wake word detection.
COHERE_API_KEY: For natural language responses.
Run the assistant:

bash
Copy code
python main.py
Usage
Activate the assistant by saying "Hey Siri".
Commands you can give:
"Play [song] on YouTube"
"Tell me a joke"
"Set a timer for [time]"
"What's the news about [topic]?"
"Open [website]"
"Shutdown assistant"
License
This project is licensed under the MIT License. See the LICENSE file for more details.