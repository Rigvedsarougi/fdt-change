from flask import Flask, request, jsonify
from app import process_audio_files process_audio_chunk detect_keywords analyze_text_for_personal_details

app = Flask(__name__)

@app.route('/process_audio', methods=['POST'])
def process_audio():
    # Get audio files from request
    audio_files = request.files.getlist('audio_files')

    # Process audio files
    keywords = [
        'Global',
        'HANA',
        'Server',
        'Software'
    ]
    results = process_audio_files(audio_files, keywords)

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
