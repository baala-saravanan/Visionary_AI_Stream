import os
import sys
import cv2
import threading
import base64
import time
import requests
from queue import Queue
from pydub import AudioSegment
from pydub.playback import play
import google.generativeai as genai
from PIL import Image
import numpy as np
import errno
import logging
from gtts import gTTS
from googletrans import Translator  # Import the Translator class

sys.path.insert(0, '/home/rock/Desktop/Hearsight/')
from play_audio import GTTSA
import playsound

play_audio = GTTSA()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set the API key for Google AI
GOOGLE_API_KEY = 'AIzaSyA6mjkdzLwXNuWM6V0SW8CxSGQw0yoCy-w'  # Replace with your actual key

# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

# Folder to save frames
folder = "frames"
if not os.path.exists(folder):
    os.makedirs(folder)

# Queue to store text responses
text_queue = Queue()

# Flag to indicate when audio playback is in progress
audio_playing = threading.Event()

# Global variables
running = True
capture_interval = 1  # Time between captures in seconds
script = []  # Initialize script outside the capture_images function

# Path to the language file
LANGUAGE_FILE_PATH = '/home/rock/Desktop/Hearsight/lang.txt'

# Language mapping for gTTS and googletrans
LANGUAGE_MAPPING = {
    'Tamil': 'ta',
    'English': 'en',
    'Kannada': 'kn',
    'Telugu': 'te',
    'Malayalam': 'ml',
    'Hindi': 'hi'
}

def read_language():
    try:
        with open(LANGUAGE_FILE_PATH, 'r') as file:
            language = file.read().strip()
        if language not in LANGUAGE_MAPPING:
            language = 'English'
    except IOError:
        language = 'English'
    
    return LANGUAGE_MAPPING[language]

def encode_image(image_path):
    while True:
        try:
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_image
        except IOError as e:
            if e.errno == errno.EACCES:
                print("Permission denied, retrying in 5 seconds...")
                time.sleep(4)
            else:
                print(f"Error {e.errno}: {e.strerror}")
                return None

def generate_audio(text, filename):
    language = read_language()
    try:
        tts = gTTS(text=text, lang=language)
        tts.save(filename)
    except Exception as e:
        logging.error(f"Error generating audio with gTTS: {e}")

def play_audio_func():
    global audio_playing
    current_audio = "voice_current.mp3"
    next_audio = "voice_next.mp3"
    while True:
        text = text_queue.get()
        if text is None:
            break
        audio_playing.set()
        try:
            generate_audio(text, next_audio)
            os.rename(next_audio, current_audio)
            playsound.playsound("voice_current.mp3")
            os.system("python3.9 /home/rock/Desktop/Hearsight/English/go_see/go_see.py")
            os._exit(0)
        except Exception as e:
            logging.error(f"Error in play_audio: {e}")
        finally:
            audio_playing.clear()

def generate_new_line(encoded_image):
    return [
        {
            "role": "user",
            "content": {
                "parts": [
                    {
                        "text": "Explain in detail what you see in this image with any texts or words to read it in below 15 words"
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": encoded_image
                        }
                    }
                ]
            }
        }
    ]

def translate_text(text, target_language):
    translator = Translator()
    try:
        translated = translator.translate(text, dest=target_language)
        return translated.text
    except Exception as e:
        logging.error(f"Error translating text: {e}")
        return text  # Return original text if translation fails

def analyze_image(encoded_image, script):
    try:
        messages = script + generate_new_line(encoded_image)
        content_messages = [
            {
                "role": message["role"],
                "parts": [
                    {"text": part["text"]} if "text" in part else {"inline_data": part["inline_data"]}
                    for part in message["content"]["parts"]
                ]
            }
            for message in messages
        ]
        response = model.generate_content(content_messages)
        return response.text
    except Exception as e:
        logging.error(f"Error in analyze_image: {e}")
        return ""

def capture_images():
    global capture_interval
    global script
    cap = cv2.VideoCapture(1)  # Assuming webcam index 1

    while running:
        try:
            ret, frame = cap.read()
            if ret:
                # Resize and compress the image
                pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                max_size = 250
                ratio = max_size / max(pil_img.size)
                new_size = tuple([int(x * ratio) for x in pil_img.size])
                resized_img = pil_img.resize(new_size, Image.LANCZOS)
                frame = cv2.cvtColor(np.array(resized_img), cv2.COLOR_RGB2BGR)

                path = f"{folder}/frame.jpg"
                cv2.imwrite(path, frame)
                print("Saving photo.")

                encoded_image = encode_image(path)
                print(f"Encoded image: {encoded_image[:30]}...")  # Debug print

                if not encoded_image:
                    print("Failed to encode image. Retrying in 5 seconds...")
                    time.sleep(4)
                    continue
                
                response_text = analyze_image(encoded_image, script)
                print(f"HearSight's response: {response_text}")

                # Translate the response_text if needed
                target_language = read_language()
                if target_language != 'en':
                    response_text = translate_text(response_text, target_language)
                    print(f"Translated response: {response_text}")

                text_queue.put(response_text)
                
                script.append(
                    {
                        "role": "model",
                        "content": {
                            "parts": [
                                {
                                    "text": response_text
                                }
                            ]
                        }
                    }
                )

                # Close the camera immediately after capturing the frame
                cap.release()

                # Wait for audio playback to finish before capturing the next frame
                while audio_playing.is_set():
                    time.sleep(0.1)

                # Wait for 5 seconds before capturing the next frame
                time.sleep(capture_interval)  # Wait for 5 seconds
                
                # Reopen the camera for the next iteration
                cap = cv2.VideoCapture(1)

            else:
                print("Failed to capture image")
        except Exception as e:
            logging.error(f"Error in capture_images: {e}")
            break

        time.sleep(0.1)  # Sleep for a short duration to avoid busy-waiting

if __name__ == '__main__':
    global capture_thread
    global audio_thread
    running = True
    capture_thread = threading.Thread(target=capture_images)
    capture_thread.start()
    audio_thread = threading.Thread(target=play_audio_func)
    audio_thread.start()

    # Keep the main thread running to capture keyboard interrupts
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected, stopping...")
        running = False
        capture_thread.join()
        text_queue.put(None)
        audio_thread.join()
