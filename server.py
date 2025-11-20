from flask import Flask, request, jsonify
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import base64
import os

app = Flask(__name__)

# تكوين Tesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

@app.route('/ocr', methods=['POST'])
def ocr():
    try:
        data = request.get_json()
        
        if not data or 'file' not in data:
            return jsonify({'success': False, 'error': 'لم يتم إرسال ملف'}), 400
        
        # فك تشفير base64
        file_data = base64.b64decode(data['file'])
        filename = data.get('filename', 'document')
        
        # تحديد نوع الملف
        is_pdf = filename.lower().endswith('.pdf') or data.get('mimetype') == 'application/pdf'
        
        if is_pdf:
            # معالجة PDF
            pages = convert_from_bytes(file_data, dpi=300)
            extracted_text = []
            
            for page_num, page in enumerate(pages, 1):
                text = pytesseract.image_to_string(page, lang='ara+eng')
                extracted_text.append(f"--- صفحة {page_num} ---\n{text}")
            
            full_text = '\n\n'.join(extracted_text)
        else:
            # معالجة صورة
            image = Image.open(io.BytesIO(file_data))
            full_text = pytesseract.image_to_string(image, lang='ara+eng')
        
        file_size_mb = len(file_data) / (1024 * 1024)
        
        return jsonify({
            'success': True,
            'text': full_text,
            'file_size_mb': round(file_size_mb, 2)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'خطأ في المعالجة: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'tesseract': 'available'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
