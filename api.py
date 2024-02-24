from flask import Flask, request, jsonify
from io import BytesIO
from app import process_audio_files

app = Flask(__name__)

@app.route('/detect_fraud', methods=['POST'])
def detect_fraud():
    # Ensure that the request contains MP3 files
    if 'audio_files' not in request.files:
        return jsonify({'error': 'No audio files found in the request'}), 400
    
    audio_files = request.files.getlist('audio_files')
    
    # Ensure that audio files are provided
    if len(audio_files) == 0:
        return jsonify({'error': 'No audio files provided'}), 400

    # Convert audio files to BytesIO objects
    audio_files_bytes = [BytesIO(audio_file.read()) for audio_file in audio_files]
    
    # Keywords for fraud detection
    keywords = ['Global', 'HANA', 'Server', 'Software']

    # Process audio files
    results = process_audio_files(audio_files_bytes, keywords)

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
