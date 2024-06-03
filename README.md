# HearSight-Visionary_AI_Stream 
This Python code is for a system called HearSight, which captures images using a webcam, analyzes them with a generative AI model, and provides spoken descriptions. The key steps are:

Initialization: Sets up logging, Google AI client, GPIO for an exit button, and directories for storing frames.
Language Handling: Reads the preferred language from a file and sets up language mappings for text-to-speech (gTTS) and translation (googletrans).
Image Capture and Encoding: Continuously captures images from the webcam, resizes and saves them, then encodes them to base64.
Image Analysis: Sends the encoded image to a generative AI model for analysis and retrieves a textual description.
Translation: Translates the description if the target language is different from English.
Audio Playback: Converts the description to speech using gTTS and plays the audio, handling a stop signal via GPIO.
Multithreading: Uses separate threads for capturing images and playing audio to ensure smooth operation.
Graceful Shutdown: Ensures the application can be stopped gracefully with a keyboard interrupt.
