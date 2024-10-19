
def main():
    global assistant_active

    # Function to activate the assistant
    def activate_assistant():
        global assistant_active
        if not assistant_active:
            assistant_active = True
            speak("Hello! I am Siri, your personal assistant. Say the wake word once to activate.")
            detect_wake_word()

            if wake_word_detected:
                speak("Yes, I'm here. How can I help?")
                while assistant_active:
                    command = listen_command()
                    if command:
                        execute_command(command)

    # Function to deactivate the assistant
    def deactivate_assistant():
        global assistant_active
        assistant_active = False
        speak("Assistant deactivated. Press the key to activate again.")

    # Define the key you want to press to activate the assistant (e.g., 'F8' key)
    activation_key = 'shift+`'

    # Listen for the activation key press
    print(f"Press {activation_key} to activate the assistant.")
    while True:
        # Check if the activation key is pressed
        if keyboard.is_pressed(activation_key):
            activate_assistant()

        # If the assistant is running and you give a shutdown command, deactivate it
        if assistant_active and "shutdown assistant" in listen_command():
            deactivate_assistant()

if __name__ == "__main__":
    main()
