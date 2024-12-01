import pytesseract
from PIL import Image
import cv2
from langdetect import detect
from mtranslate import translate
import pyttsx3
from flask import Flask, request, render_template, jsonify
import os

app = Flask(__name__)

# Set the path to the Tesseract executable (if needed)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Function to preprocess image (optional step to improve OCR accuracy)
def preprocess_image(image_path):
    # Read image using OpenCV
    img = cv2.imread(image_path)
    
    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply binary thresholding (invert colors to white text on black background)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Optionally, save the processed image (for debugging)
    cv2.imwrite("processed_image.png", thresh)
    
    return thresh

# Function to extract text from image using Tesseract OCR
def extract_text_from_image(image_path, lang='eng+tel+hin'):  # Support for multiple languages (Telugu and Hindi)
    # Preprocess the image (optional)
    processed_image = preprocess_image(image_path)
    
    # Open image using Pillow (PIL) for pytesseract
    img = Image.open(image_path)
    
    # Perform OCR to extract text, specify multiple languages (Telugu: 'tel', Hindi: 'hin', English: 'eng')
    text = pytesseract.image_to_string(img, lang=lang)
    return text

# Function to detect the language of the extracted text using langdetect
def detect_language(text):
    try:
        # Detect language of the text
        language = detect(text)
        if language == 'te':
            return 'Telugu'
        elif language == 'hi':
            return 'Hindi'
        else:
            return language  # Return the detected language code (for other cases)
    except Exception as e:
        return "Error in language detection"

# Function to translate text using mtranslate
def translate_text(text, target_lang='en', source_lang='te'):
    translated_text = translate(text, target_lang, source_lang)
    return translated_text

# Function to convert text to speech with added adjustments
def speak_text(text):
    # Initialize pyttsx3 engine
    engine = pyttsx3.init()

    # Set properties (rate of speech, voice type)
    rate = engine.getProperty('rate')   # Get the current rate of speech
    engine.setProperty('rate', rate - 50)  # Slow down the speech (optional)

    voices = engine.getProperty('voices')  # Get the list of available voices
    engine.setProperty('voice', voices[1].id)  # Set voice (1 for female, 0 for male in most cases)

    # Speak the text
    engine.say(text)
    engine.runAndWait()  # Wait until speech is finished

# Route for rendering the upload page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle the image upload and process it
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({"error": "No file part"})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    
    if file:
        # Save the uploaded file
        image_path = os.path.join('uploads', file.filename)
        file.save(image_path)
        
        # Extract text from the uploaded image
        extracted_text = extract_text_from_image(image_path, lang='eng+tel+hin')
        
        # Detect the language of the extracted text
        language = detect_language(extracted_text)
        
        # If the detected language is Telugu or Hindi, translate it to English
        if language == 'Telugu':  # Check for the human-readable "Telugu"
            translated_text = translate_text(extracted_text, target_lang='en', source_lang='te')
            
            # Remove the uploaded image file after processing
            os.remove(image_path)
            
            return jsonify({
                "extracted_text": extracted_text,
                "detected_language": language,
                "translated_text": translated_text
            })
        elif language == 'Hindi':  # Check for the human-readable "Hindi"
            translated_text = translate_text(extracted_text, target_lang='en', source_lang='hi')
            
            # Remove the uploaded image file after processing
            os.remove(image_path)
            
            return jsonify({
                "extracted_text": extracted_text,
                "detected_language": language,
                "translated_text": translated_text
            })
        else:
            # Return the original extracted text (if not translated)
            os.remove(image_path)
            
            return jsonify({
                "extracted_text": extracted_text,
                "detected_language": language
            })
    
    return jsonify({"error": "File not processed"})

# New Route to handle Text-to-Speech requests
@app.route('/speak', methods=['POST'])
def speak():
    data = request.get_json()
    text = data.get('text', '')

    if text:
        # Call the text-to-speech function (pyttsx3)
        speak_text(text)  # Assuming `speak_text` function is defined in the backend

        return jsonify({"status": "success", "message": "Speech synthesis started."})
    else:
        return jsonify({"status": "error", "message": "No text provided for speech synthesis."})

if __name__ == '__main__':
    app.run(debug=True)

# http://127.0.0.1:5000/