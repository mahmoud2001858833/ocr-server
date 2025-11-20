from flask import Flask, request, jsonify
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import requests
import os

app = Flask(__name__)

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

@app.route('/ocr', methods=['POST'])
def ocr():
    try:
        data = request.get_json()
        
        if not data or 'file_url' not in data:
            return jsonify({'success': False, 'error': 'لم يتم إرسال رابط الملف'}), 400
        
        file_url = data['file_url']
        filename = data.get('filename', 'document')
        
        print(f'Downloading from: {file_url}')
        response = requests.get(file_url, timeout=120)
        
        if response.status_code != 200:
            return jsonify({'success': False, 'error': f'فشل التحميل: {response.status_code}'}), 400
        
        file_data = response.content
        file_size_mb = len(file_data) / (1024 * 1024)
        print(f'Size: {file_size_mb:.2f} MB')
        
        is_pdf = filename.lower().endswith('.pdf')
        
        if is_pdf:
            print('Converting PDF...')
            pages = convert_from_bytes(file_data, dpi=300)
            print(f'{len(pages)} pages')
            
            extracted_text = []
            for page_num, page in enumerate(pages, 1):
                print(f'Page {page_num}...')
                text = pytesseract.image_to_string(page, lang='ara+eng')
                extracted_text.append(f"--- صفحة {page_num} ---\n{text}")
            
            full_text = '\n\n'.join(extracted_text)
        else:
            image = Image.open(io.BytesIO(file_data))
            full_text = pytesseract.image_to_string(image, lang='ara+eng')
        
        print(f'Done: {len(full_text)} chars')
        
        return jsonify({
            'success': True,
            'text': full_text,
            'file_size_mb': round(file_size_mb, 2)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
