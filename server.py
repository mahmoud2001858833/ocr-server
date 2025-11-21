from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import requests

app = Flask(__name__)
CORS(app)

@app.route('/ocr', methods=['POST'])
def ocr():
    try:
        data = request.get_json()
        
        if not data or 'file_url' not in data:
            return jsonify({
                'success': False,
                'error': 'لم يتم إرسال رابط الملف'
            }), 400
        
        file_url = data['file_url']
        filename = data.get('filename', 'unknown')
        
        print(f'Processing file: {filename}')
        print(f'Downloading from URL: {file_url}')
        
        # Download the file
        response = requests.get(file_url, timeout=60)
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'فشل تحميل الملف: {response.status_code}'
            }), 400
        
        file_bytes = response.content
        file_size_mb = len(file_bytes) / (1024 * 1024)
        print(f'Downloaded {file_size_mb:.2f} MB')
        
        # Convert PDF to images
        print('Converting PDF to images...')
        images = convert_from_bytes(file_bytes, dpi=200)
        print(f'Converted to {len(images)} pages')
        
        # Extract text from each page
        print('Extracting text with Tesseract...')
        extracted_text = []
        for i, image in enumerate(images, 1):
            print(f'Processing page {i}/{len(images)}')
            text = pytesseract.image_to_string(image, lang='ara+eng')
            if text.strip():
                extracted_text.append(text)
        
        full_text = '\n\n'.join(extracted_text)
        
        if not full_text.strip():
            return jsonify({
                'success': False,
                'error': 'لم يتم استخراج أي نص من الملف'
            }), 400
        
        print(f'Extracted {len(full_text)} characters')
        
        return jsonify({
            'success': True,
            'text': full_text,
            'file_size_mb': round(file_size_mb, 2),
            'pages_count': len(images)
        })
        
    except Exception as e:
        print(f'Error: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
