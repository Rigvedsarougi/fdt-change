import os
import re
from multiprocessing import Pool
from functools import partial
import pandas as pd
from pydub import AudioSegment
import speech_recognition as sr
import streamlit as st
import tempfile
import logging

logging.basicConfig(level=logging.DEBUG)

def analyze_text_for_personal_details(text):
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    phone_pattern = re.compile(r'\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})\b')
    personal_account_pattern = re.compile(r'\b(?:personal account)\b', re.IGNORECASE)

    emails_found = re.findall(email_pattern, text)
    phones_found = re.findall(phone_pattern, text)
    personal_account_detected = bool(re.search(personal_account_pattern, text))

    return emails_found, phones_found, personal_account_detected

def detect_keywords(input_text, keywords):
    keyword_presence = {keyword: bool(re.search(re.escape(keyword), input_text, re.IGNORECASE)) for keyword in keywords}
    return keyword_presence

def process_audio_chunk(chunk, recognizer, language='en-US'):
    try:
        chunk.export("temp.wav", format="wav")
        with sr.AudioFile("temp.wav") as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, show_all=True, language=language)  
            if 'alternative' in text:
                text = text['alternative'][0]['transcript']
            return text
    except Exception as e:
        logging.error(f"Error processing audio chunk: {e}")
        return ""

def process_audio_file(audio_file, languages, keywords):
    recognizer = sr.Recognizer()
    results = []
    
    for language in languages:
        # Save BytesIO to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_audio_file:
            temp_audio_file.write(audio_file.read())

        # Load temporary file with pydub
        audio = AudioSegment.from_mp3(temp_audio_file.name)

        chunk_size_ms = 5000
        chunks = [audio[i:i + chunk_size_ms] for i in range(0, len(audio), chunk_size_ms)]

        for i, chunk in enumerate(chunks):
            text = process_audio_chunk(chunk, recognizer, language)
            if text:
                results.append((language, text))

    transcriptions = {lang: " ".join([text for lang_, text in results if lang_ == lang]) for lang in languages}
    
    all_emails = []
    all_phones = []
    personal_account_detected = False

    for language, transcription in transcriptions.items():
        emails, phones, personal_account = analyze_text_for_personal_details(transcription)
        all_emails.extend(emails)
        all_phones.extend(phones)
        personal_account_detected = personal_account_detected or personal_account

    keyword_results = {}
    for language, transcription in transcriptions.items():
        keyword_results[language] = detect_keywords(transcription, keywords)

    result = {
        'File Name': audio_file.name,
        'Transcriptions': transcriptions,
        'Fraud Detection': {lang: 'Fraud detected' if any(keyword_results[lang].values()) else 'Not fraud detected' for lang in languages},
        **keyword_results,
        'Personal Account Detection': 'Personal account detected' if personal_account_detected else 'Personal account not detected',
        'Personal Details': {'Emails': all_emails, 'Phones': all_phones}
    }

    return result

def process_audio_files(audio_files, languages, keywords):
    results = []

    for audio_file in audio_files:
        result = process_audio_file(audio_file, languages, keywords)
        results.append(result)

    return results

def main():
    st.title("Multilingual Audio Fraud Detection")

    audio_files = st.file_uploader("Upload MP3 audio files", type=["mp3"], accept_multiple_files=True)

    languages = st.multiselect("Select Languages", options=["en-US", "hi-IN", "es-ES"], default=["en-US"])
    
    if audio_files and languages:
        keywords = [
            'Global',
            'HANA',
            'Server',
            'Software'
        ]

        results = process_audio_files(audio_files, languages, keywords)
        result_df = pd.DataFrame(results)
        st.write(result_df)
        csv_data = result_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download File",
            data=csv_data,
            file_name="audio_fraud_detection_results.csv",
            key="download_button"
        )

if __name__ == "__main__":
    main()
