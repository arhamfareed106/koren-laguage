import os
from flask import Flask, request, render_template, jsonify
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
import re

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_and_translate_text(image_path):
    """Extract text from an image and translate it to English."""
    try:
        # Perform OCR to extract text from the image
        original_text = pytesseract.image_to_string(Image.open(image_path), lang='kor')
        
        # Translate the extracted text from Korean to English
        translator = GoogleTranslator(source='ko', target='en')
        translated_text = translator.translate(text=original_text if original_text else "No text found")
        
        return original_text, translated_text
    except Exception as e:
        print(f"Error in extraction/translation: {str(e)}")
        return "", ""

def parse_fields(text):
    """Parse specific fields dynamically from translated text."""
    # Define regex patterns to detect specific fields
    name_pattern = r"(name\s*[:\-]\s*(.+?)(?=\n|$))"
    phone_pattern = r"(phone\s*[:\-]\s*(.+?)(?=\n|$))"
    address_pattern = r"(address\s*[:\-]\s*(.+?)(?=\n|$))"
    type_pattern = r"(type of information\s*[:\-]\s*(.+?)(?=\n|$))"

    # Extract data for each field
    name = re.search(name_pattern, text, re.IGNORECASE)
    phone = re.search(phone_pattern, text, re.IGNORECASE)
    address = re.search(address_pattern, text, re.IGNORECASE)
    info_type = re.search(type_pattern, text, re.IGNORECASE)

    return {
        "Name": name.group(2).strip() if name else "Not found",
        "Phone": phone.group(2).strip() if phone else "Not found",
        "Address": address.group(2).strip() if address else "Not found",
        "Type of Information": info_type.group(2).strip() if info_type else "Not found"
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        # Save the uploaded file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Process the image
        original_text, translated_text = extract_and_translate_text(filepath)
        
        # Parse the fields
        fields = parse_fields(translated_text)

        # Clean up - remove the uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

        return jsonify(fields)

@app.route('/test-tesseract')
def test_tesseract():
    """Test if Tesseract OCR is properly installed and configured."""
    try:
        version = pytesseract.get_tesseract_version()
        languages = pytesseract.get_languages()
        return jsonify({
            'status': 'success',
            'version': str(version),
            'languages': languages,
            'tesseract_cmd': pytesseract.pytesseract.tesseract_cmd
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
