# Author: NKONO NDEME Miguel

from collections.abc import Generator
from pathlib import Path
from typing import Any, Optional

import os
import subprocess
import librosa
import numpy as np

from ingestion.config import *


def load_audio_files(path: str) -> Generator[Path, Any, None]:
    """
    This function is going to recursively return audio file from a direction and its sub-directories.
    """
    for dirpath, _, filenames in os.walk(path):
        if "converted" in Path(dirpath).parts:
            continue

        for file in filenames:
            audio_path: Path = Path(dirpath) / file

            if Path(audio_path).suffix.lower() in SUPPORT_EXT:
                yield audio_path


def convert_audio_file(audio_path: str) -> Optional[str]:
    """
    Convert an audio/video file to a 16 kHz mono PCM WAV using FFmpeg.
    """

    input_file = Path(audio_path)
    root = input_file.parts[:1]
    root = '/'.join(root)
    root = Path(root) / "converted"
    root.mkdir(parents=True, exist_ok=True)
    output_audio_file = root / f"{input_file.stem}.wav"
    print(output_audio_file)

    command = [
        'ffmpeg',
        '-y',
        '-i', audio_path,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        output_audio_file
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, timeout=120)
        return str(output_audio_file)
        # return str(CONVERTION_LOCATION)

    except subprocess.TimeoutExpired:
        reason = "ffmpeg conversion timed out (>120s)"
        logger.error(f"'{audio_path}': {reason}")
        return None

    except subprocess.CalledProcessError as e:
        # Extract only the last meaningful line from stderr
        stderr_lines = e.stderr.decode().splitlines()
        last_error = next(
            (l for l in reversed(stderr_lines)
             if l.strip() and not l.startswith('  ')),
            "unknown ffmpeg error"
        )
        reason = f"ffmpeg error: {last_error}"
        logger.error(f"'{audio_path}': {reason}")
        return None


def normalize_audio(converted_audio_path: str) -> (tuple[np.ndarray, int | float, str] | None):
    """
    This function is going to normalized an audio file.
    """

    audio_time_series: np.ndarray
    sampling_rate: int | float
    audio_time_series, sampling_rate = librosa.load(converted_audio_path, sr=None)

    # discard audio that have a duration of 1.5s
    if len(audio_time_series) / sampling_rate < 1.5:
        return None

    max_val = np.max(np.abs(audio_time_series))
    if max_val == 0:
        return None

    normalized_audio: np.ndarray
    normalized_audio = GAIN * audio_time_series / max_val

    return normalized_audio, sampling_rate, converted_audio_path


def loads(audio_paths: str) -> Generator[tuple[np.ndarray, int | float, str], Any, None]:
    """
    This function is going to load all the audio files containt in a director,
    converted them to PCM 16-bit mono,
    normalize them and return them.
    """

    for audio_file in load_audio_files(audio_paths):
        converted_audio = convert_audio_file(str(audio_file))
        if converted_audio is None:
            logger.info(f"{audio_file} not loaded correctly")
            continue

        normalized_audio = normalize_audio(converted_audio)
        if normalized_audio is None:
            logger.error(f"Can'a normalize this {audio_file} audio file")
            continue

        yield normalized_audio
