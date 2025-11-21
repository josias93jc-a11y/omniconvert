import os
from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
from pdf2docx import Converter
from werkzeug.utils import secure_filename
from PIL import Image
import uuid

# Configura pastas estáticas para servir o HTML e CSS/JS se necessário
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

UPLOAD_FOLDER = '/tmp/uploads'  # Usar /tmp é crucial em nuvens como Render/Heroku
OUTPUT_FOLDER = '/tmp/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# --- FUNÇÕES DE CONVERSÃO ---
def convert_pdf_to_docx(pdf_path, docx_path):
    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        return True
    except Exception as e:
        print(f"Erro PDF: {e}")
        return False


def convert_image(input_path, output_path, target_format):
    try:
        with Image.open(input_path) as img:
            rgb_im = img.convert('RGB')
            rgb_im.save(output_path)
        return True
    except Exception as e:
        print(f"Erro Imagem: {e}")
        return False


# --- ROTA PRINCIPAL (SERVE O SITE) ---
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')


# --- ROTA DE CONVERSÃO ---
@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    target_format = request.form.get('targetFormat', 'docx').lower()

    if file.filename == '':
        return jsonify({'error': 'Nome inválido'}), 400

    if file:
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        unique_id = str(uuid.uuid4())

        input_filename = f"{unique_id}_{original_filename}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        file.save(input_path)

        base_name_original = original_filename.rsplit('.', 1)[0]
        final_download_name = f"{base_name_original}_Convert.{target_format}"

        output_filename = f"{unique_id}_converted.{target_format}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        success = False

        if file_ext == 'pdf' and target_format == 'docx':
            success = convert_pdf_to_docx(input_path, output_path)
        elif file_ext in ['jpg', 'jpeg', 'png', 'bmp', 'webp'] and target_format in ['pdf', 'png', 'jpg', 'jpeg']:
            success = convert_image(input_path, output_path, target_format)

        if success:
            try:
                os.remove(input_path)
            except:
                pass
            return send_file(output_path, as_attachment=True, download_name=final_download_name)
        else:
            return jsonify({'error': 'Formato não suportado no Backend Lite.'}), 500


if __name__ == '__main__':
    # Em produção, o Gunicorn vai chamar o 'app', mas localmente usamos isso:
    app.run(debug=True, port=5000)