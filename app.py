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

def process_audio_chunk(chunk, recognizer):
    try:
        chunk.export("temp.wav", format="wav")
        with sr.AudioFile("temp.wav") as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, show_all=True, language='en-US')  # Adjust parameters
            if 'alternative' in text:
                text = text['alternative'][0]['transcript']
            return text
    except Exception as e:
        logging.error(f"Error processing audio chunk: {e}")
        return ""

def process_audio_file(audio_file, keywords):
    recognizer = sr.Recognizer()

    # Load temporary file with pydub
    audio = AudioSegment.from_file(audio_file)

    chunk_size_ms = 5000
    chunks = [audio[i:i + chunk_size_ms] for i in range(0, len(audio), chunk_size_ms)]

    results = []
    unrecognized_chunks_count = 0

    for i, chunk in enumerate(chunks):
        text = process_audio_chunk(chunk, recognizer)
        if text:
            results.append(text)
        else:
            unrecognized_chunks_count += 1

    transcription = " ".join(results)

    emails, phones, personal_account_detected = analyze_text_for_personal_details(transcription)

    keyword_results = detect_keywords(transcription, keywords)

    total_chunks = len(chunks)
    percentage_unrecognized = (unrecognized_chunks_count / total_chunks) * 100 if total_chunks > 0 else 0

    result = {
        'File Name': audio_file.name,
        'Transcription': transcription,
        'Fraud Detection': 'Fraud detected' if any(keyword_results.values()) else 'Not fraud detected',
        **keyword_results,
        'Personal Account Detection': 'Personal account detected' if personal_account_detected else 'Personal account not detected',
        'Personal Details': {'Emails': emails, 'Phones': phones}
    }

    return result

@st.experimental_singleton
def main():
    st.title("Audio Fraud Detection")

    # Receive file uploads via POST request
    audio_files = st.file_uploader("Upload MP3 audio files", type=["mp3"], accept_multiple_files=True)

    if audio_files:
        keywords = [
            'Global',
            'HANA',
            'Server',
            'Software'
        ]

        results = process_audio_files(audio_files, keywords)
        result_df = pd.DataFrame(results)
        st.write(result_df.to_json())

def process_audio_files(audio_files, keywords):
    results = []

    for audio_file in audio_files:
        result = process_audio_file(audio_file, keywords)
        results.append(result)

    return results

if __name__ == "__main__":
    main()
