from flask import Blueprint, send_from_directory, abort, send_file
from config import DETECTION_DIR_NAME
import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import io
import numpy as np

audio_files_blueprint = Blueprint('audio_files', __name__)

basedir = os.path.dirname(os.path.abspath(__file__))
DETECTION_DIR = os.path.join(basedir, '..', '..', DETECTION_DIR_NAME)


@audio_files_blueprint.route('/audio-files/<path:filename>')
def serve_audio_file(filename):
    try:
        return send_from_directory(DETECTION_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)


@audio_files_blueprint.route('/spectrogram/<path:filename>.png')
def serve_spectrogram(filename):

    audio_path = os.path.join(DETECTION_DIR, filename)

    if not os.path.exists(audio_path):
        abort(404)

    y, sr = librosa.load(audio_path)
    plt.figure(figsize=(10, 4))
    D = librosa.amplitude_to_db(librosa.stft(y), ref=np.max)
    librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Spectrogram')

    image_binary = io.BytesIO()
    plt.savefig(image_binary, format='png')
    image_binary.seek(0)
    plt.close()

    return send_file(image_binary, mimetype='image/png')
