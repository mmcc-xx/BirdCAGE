from flask import Blueprint, send_from_directory, abort, send_file
from config import DETECTION_DIR_NAME
import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import io
import numpy as np
import subprocess
from pathlib import Path

audio_files_blueprint = Blueprint('audio_files', __name__)

basedir = os.path.dirname(os.path.abspath(__file__))
DETECTION_DIR = os.path.join(basedir, '..', '..', DETECTION_DIR_NAME)


@audio_files_blueprint.route('/api/audio-files/<path:filename>')
def serve_audio_file(filename):
    try:
        return send_from_directory(DETECTION_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)


@audio_files_blueprint.route('/api/spectrogram/<path:filename>.png')
def serve_spectrogram(filename):

    audio_path = os.path.join(DETECTION_DIR, filename)

    if not os.path.exists(audio_path):
        abort(404)

    # Load the audio file, mix it down to mono, and resample it to 24000 Hz
    y, sr = librosa.load(audio_path, sr=24000, mono=True)

    # Compute the Short-Time Fourier Transform (STFT) with a Hann window
    #D = librosa.stft(y, n_fft=2048, hop_length=512, win_length=2048, window='hann')
    D = librosa.stft(y, n_fft=4096, hop_length=128, win_length=4096, window='hann')

    # Convert the STFT to decibels
    D_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)


    # Generate the spectrogram image
    plt.figure(figsize=(10, 4))
    #librosa.display.specshow(D_db, sr=24000, hop_length=512, x_axis='time', y_axis='linear')
    librosa.display.specshow(D_db, sr=24000, hop_length=128, x_axis='time', y_axis='linear')
    plt.colorbar(format='%+2.0f dB')

    image_binary = io.BytesIO()
    plt.savefig(image_binary, format='png')
    image_binary.seek(0)
    plt.close()

    return send_file(image_binary, mimetype='image/png')
