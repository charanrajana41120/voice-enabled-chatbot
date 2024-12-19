import openai
import pyttsx3
import speech_recognition as sr
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from openai.error import RateLimitError

# Flask application setup
app = Flask(__name__)
socketio = SocketIO(app)

# OpenAI API Key
openai.api_key = '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'

# Function to convert speech to text
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        
    try:
        text = recognizer.recognize_google(audio)
        print("You said: " + text)
        return text
    except sr.UnknownValueError:
        print("Sorry, I didn't understand that.")
        return None
    except sr.RequestError:
        print("Could not request results from Google Speech Recognition service.")
        return None

# Function to interact with GPT-3
def chat_with_gpt3(input_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-4" if you have access
            messages=[{"role": "user", "content": input_text}],
        )
        response_text = response['choices'][0]['message']['content'].strip()
        return response_text
    except RateLimitError:
        return "Sorry, the service is currently busy. Please try again later."

# Function to convert text to speech
def text_to_speech(response_text):
    engine = pyttsx3.init()
    engine.say(response_text)
    engine.runAndWait()

# Check if the message contains exit phrases
def should_exit(user_input):
    exit_phrases = ['no thanks', 'see you later', 'ok thank you', 'bye', 'goodbye']
    return any(phrase in user_input.lower() for phrase in exit_phrases)

# Route to render the main page
@app.route('/')
def index():
    return render_template('index.html')

# SocketIO event to handle voice input and response
@socketio.on('start_voice_chat')
def handle_voice_chat(message):
    while True:
        user_input = speech_to_text()
        if user_input:
            if should_exit(user_input):  # Check if the exit phrase is spoken
                emit('bot_response', {'response': "Goodbye! Have a great day!"})
                break  # Exit the loop if the user says "bye", "goodbye", etc.
            emit('user_input', {'input': user_input})  # Emit the user's input to the chat area
            response_text = chat_with_gpt3(user_input)
            emit('bot_response', {'response': response_text})
            text_to_speech(response_text)

# SocketIO event to handle text input and response
@socketio.on('start_text_chat')
def handle_text_chat(message):
    user_input = message['text']
    if should_exit(user_input):  # Check if the exit phrase is typed
        emit('bot_response', {'response': "Goodbye! Have a great day!"})
    else:
        emit('user_input', {'input': user_input})  # Emit the user's input to the chat area
        response_text = chat_with_gpt3(user_input)
        emit('bot_response', {'response': response_text})

if __name__ == "__main__":
    socketio.run(app)
