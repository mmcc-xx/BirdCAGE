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
THUMB_DIR = os.path.join(DETECTION_DIR, 'thumb')
FULL_DIR = os.path.join(DETECTION_DIR, 'full')

def create_spectrogram(fn_audio, height=50, ratio=2):
    clip, sample_rate = librosa.load(fn_audio, sr=None)
    S = librosa.feature.melspectrogram(y=clip, sr=sample_rate)
    S_db = librosa.power_to_db(S, ref=np.max)

    # Set the desired output image size (height = 100, width = 200)
    output_height = height
    output_width = height * ratio

    # Calculate the new figure size based on the desired output image size
    dpi = 100
    fig_height = output_height / dpi
    fig_width = output_width / dpi

    # Create a new figure with the calculated figsize
    fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
    plt.gca().set_axis_off()

    # Display the spectrogram with the specified width and height
    plt.imshow(S_db, extent=(0, output_width, 0, output_height), aspect='auto', origin='lower')

    # Save the plot to an in-memory binary stream
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)

    # Read the content of the buffer as a byte array
    png_data = buf.getvalue()

    # Close the binary stream and the figure
    buf.close()
    plt.close(fig)

    # Return the byte array
    return png_data


@audio_files_blueprint.route('/api/audio-files/<path:filename>')
def serve_audio_file(filename):
    try:
        return send_from_directory(DETECTION_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)


@audio_files_blueprint.route('/api/spectrogram/thumb/<path:filename>.png')
def serve_thumb_spectrogram(filename):
    audio_path = os.path.join(DETECTION_DIR, filename)

    if not os.path.exists(audio_path):
        abort(404)

    # Create the thumb directory if it doesn't exist
    if not os.path.exists(THUMB_DIR):
        os.makedirs(THUMB_DIR)

    thumb_path = os.path.join(THUMB_DIR, f'{filename}.png')

    # check if the file exists and is bigger than 2KB. create_spectrogram seems to return empty pngs sometime
    if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) < 2 * 1024:
        image_binary = create_spectrogram(audio_path, height=70)
        # Save the thumbnail to the thumb directory
        with open(thumb_path, 'wb') as thumb_file:
            thumb_file.write(image_binary)

    return send_file(thumb_path, mimetype='image/png')


@audio_files_blueprint.route('/api/spectrogram/<path:filename>.png')
def serve_spectrogram(filename):
    audio_path = os.path.join(DETECTION_DIR, filename)

    if not os.path.exists(audio_path):
        abort(404)

        # Create the FULL_DIR directory if it doesn't exist
    if not os.path.exists(FULL_DIR):
        os.makedirs(FULL_DIR)

    full_path = os.path.join(FULL_DIR, f'{filename}.png')

    # check if the file already exists and is bigger than 10KB
    if not os.path.exists(full_path) or os.path.getsize(full_path) < 10 * 1024:
        image_binary = create_spectrogram(audio_path, height=800)
        # Save the full-size spectrogram to the FULL_DIR directory
        with open(full_path, 'wb') as full_file:
            full_file.write(image_binary)

    return send_file(full_path, mimetype='image/png')
