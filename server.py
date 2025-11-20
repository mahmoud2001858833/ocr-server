from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import os
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_CMD', '/usr/bin/tesseract')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'OCR Server'}), 200

@app.route('/ocr', methods=['POST'])
def extract_text():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'لم يتم إرسال ملف'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'اسم الملف فارغ'}), 400
        
        file_bytes = file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        
        logger.info(f"معالجة ملف: {file.filename} - الحجم: {file_size_mb:.2f} MB")
        
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        extracted_text = ""
        
        if file_extension == 'pdf':
            logger.info("تحويل PDF إلى صور...")
            images = convert_from_bytes(
                file_bytes,
                dpi=200,
                fmt='jpeg',
                thread_count=4
            )
            
            logger.info(f"عدد الصفحات: {len(images)}")
            
            for i, image in enumerate(images, 1):
                logger.info(f"معالجة الصفحة {i}/{len(images)}")
                
                page_text = pytesseract.image_to_string(
                    image,
                    lang='ara+eng',
                    config='--psm 1 --oem 3'
                )
                
                extracted_text += f"\n--- صفحة {i} ---\n{page_text.strip()}\n"
        
        elif file_extension in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff']:
            logger.info("معالجة صورة...")
            image = Image.open(io.BytesIO(file_bytes))
            
            extracted_text = pytesseract.image_to_string(
                image,
                lang='ara+eng',
                config='--psm 1 --oem 3'
            )
        
        else:
            return jsonify({'error': f'نوع الملف غير مدعوم: {file_extension}'}), 400
        
        if not extracted_text or not extracted_text.strip():
            return jsonify({'error': 'لم يتم استخراج أي نص من الملف'}), 400
        
        text_length = len(extracted_text.strip())
        logger.info(f"تم استخراج {text_length} حرف بنجاح")
        
        return jsonify({
            'success': True,
            'text': extracted_text.strip(),
            'text_length': text_length,
            'file_size_mb': round(file_size_mb, 2)
        }), 200
    
    except Exception as e:
        logger.error(f"خطأ في المعالجة: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'فشل استخراج النص: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)

