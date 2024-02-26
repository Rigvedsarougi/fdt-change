from flask import Flask, request, jsonify
from app import process_audio_files
import pandas as pd

app = Flask(__name__)

@app.route('/audio_fraud_detection', methods=['POST'])
def audio_fraud_detection():
    audio_files = request.files.getlist("audio_files")
    keywords = [
        'Global',
        'HANA',
        'Server',
        'Software'
    ]
    results = process_audio_files(audio_files, keywords)
    result_df = pd.DataFrame(results)
    return result_df.to_json(orient="records")

if __name__ == "__main__":
    app.run(debug=True)
