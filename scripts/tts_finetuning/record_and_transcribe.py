"""Voice recording with automatic transcription.

Records your voice and auto-transcribes using Whisper.
Perfect for collecting natural speech samples.

Requirements:
    pip install sounddevice soundfile openai-whisper torch

Usage:
    python scripts/tts_finetuning/record_and_transcribe.py

Output:
    scripts/tts_finetuning/recordings/
        001.wav, 002.wav, ...
        transcript.txt (auto-generated)
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Check and install dependencies
def install_deps():
    required = {
        'sounddevice': 'sounddevice',
        'soundfile': 'soundfile',
        'whisper': 'openai-whisper',
        'torch': 'torch',
    }
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Installing: {', '.join(missing)}")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)

install_deps()

import sounddevice as sd
import soundfile as sf
import whisper
import torch

# Configuration
SAMPLE_RATE = 22050  # XTTS-v2 preferred
CHANNELS = 1
OUTPUT_DIR = Path(__file__).parent / "recordings"
WHISPER_MODEL = "base"  # Options: tiny, base, small, medium, large

# Global whisper model (loaded once)
_whisper_model = None


def get_whisper_model():
    """Load Whisper model (cached)."""
    global _whisper_model
    if _whisper_model is None:
        print(f"Loading Whisper '{WHISPER_MODEL}' model...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _whisper_model = whisper.load_model(WHISPER_MODEL, device=device)
        print(f"  Loaded on {device}")
    return _whisper_model


def record_audio(max_duration: float = 30.0) -> tuple:
    """Record audio until user presses Enter.

    Returns:
        Tuple of (audio_data, sample_rate, duration)
    """
    print(f"\n  Recording... (max {max_duration}s)")
    print("  Press ENTER when done speaking")

    # Start recording
    recording = sd.rec(
        int(max_duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='float32'
    )

    # Wait for enter
    import threading
    stop_event = threading.Event()

    def wait_for_enter():
        input()
        stop_event.set()
        sd.stop()

    thread = threading.Thread(target=wait_for_enter, daemon=True)
    thread.start()

    start_time = time.time()
    while not stop_event.is_set() and (time.time() - start_time) < max_duration:
        time.sleep(0.1)

    sd.stop()

    elapsed = time.time() - start_time
    samples = int(min(elapsed, max_duration) * SAMPLE_RATE)
    audio = recording[:samples]

    return audio, SAMPLE_RATE, elapsed


def transcribe_audio(audio_path: Path) -> str:
    """Transcribe audio file using Whisper."""
    model = get_whisper_model()
    result = model.transcribe(str(audio_path), language="en")
    return result["text"].strip()


def main():
    """Main recording and transcription session."""
    print("=" * 60)
    print("Voice Recording with Auto-Transcription")
    print("=" * 60)

    # Show device info
    print(f"\nUsing device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    print(f"Whisper model: {WHISPER_MODEL}")
    print(f"Output: {OUTPUT_DIR}")

    print("\nInstructions:")
    print("  1. Speak naturally about anything")
    print("  2. Press ENTER when done")
    print("  3. I'll auto-transcribe what you said")
    print("  4. Confirm or re-record")
    print("  5. Type 'q' to quit")
    print("\nSuggested topics to talk about:")
    print("  - Describe your day")
    print("  - Explain how to make coffee")
    print("  - Give directions to a place")
    print("  - Tell a short story")
    print("  - Read some text aloud")

    # Create output dir
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Find starting index
    existing = list(OUTPUT_DIR.glob("*.wav"))
    file_index = len(existing) + 1

    # Open transcript file
    transcript_path = OUTPUT_DIR / "transcript.txt"
    transcript_mode = 'a' if existing else 'w'

    # Calculate total duration
    total_duration = 0.0
    for wav in existing:
        info = sf.info(wav)
        total_duration += info.duration

    print(f"\nExisting recordings: {len(existing)}")
    print(f"Total duration: {total_duration/60:.1f} minutes")
    print(f"\nTarget: 30 minutes for good fine-tuning")

    input("\nPress ENTER to start recording...")

    with open(transcript_path, transcript_mode, encoding='utf-8') as tf:
        while True:
            filename = f"{file_index:03d}.wav"
            filepath = OUTPUT_DIR / filename

            print(f"\n{'='*40}")
            print(f"Recording #{file_index}")
            print(f"Total so far: {total_duration/60:.1f} min")
            print(f"{'='*40}")

            # Record
            audio, sr, duration = record_audio()

            if duration < 1.0:
                print("  Too short, try again.")
                continue

            # Save temp file for transcription
            sf.write(filepath, audio, sr)
            print(f"  Recorded {duration:.1f}s")

            # Transcribe
            print("  Transcribing...")
            try:
                transcript = transcribe_audio(filepath)
                print(f"\n  Transcript: \"{transcript}\"")
            except Exception as e:
                print(f"  Transcription error: {e}")
                transcript = ""

            # Confirm
            print("\n  Options:")
            print("    ENTER = Save and continue")
            print("    r = Re-record")
            print("    e = Edit transcript")
            print("    q = Quit")

            action = input("  Choice: ").strip().lower()

            if action == 'q':
                filepath.unlink()  # Remove unsaved
                break
            elif action == 'r':
                filepath.unlink()
                print("  Discarded. Recording again...")
                continue
            elif action == 'e':
                new_transcript = input("  Enter correct transcript: ").strip()
                if new_transcript:
                    transcript = new_transcript

            # Save
            if transcript:
                tf.write(f"{filename}|{transcript}\n")
                tf.flush()
                total_duration += duration
                file_index += 1
                print(f"  Saved: {filename}")
            else:
                filepath.unlink()
                print("  No transcript, discarded.")

    # Summary
    print("\n" + "=" * 60)
    print("Session Complete!")
    print("=" * 60)

    final_count = len(list(OUTPUT_DIR.glob("*.wav")))
    final_duration = sum(sf.info(f).duration for f in OUTPUT_DIR.glob("*.wav"))

    print(f"\nTotal recordings: {final_count}")
    print(f"Total duration: {final_duration/60:.1f} minutes")
    print(f"Output: {OUTPUT_DIR}")

    if final_duration >= 1800:  # 30 min
        print("\nExcellent! You have enough for high-quality fine-tuning!")
    elif final_duration >= 600:  # 10 min
        print("\nGood start! 30 minutes recommended for best results.")
    else:
        print(f"\nKeep going! Need {(1800-final_duration)/60:.0f} more minutes.")


if __name__ == "__main__":
    main()
