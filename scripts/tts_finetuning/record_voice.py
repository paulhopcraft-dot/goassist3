"""Voice recording script for TTS fine-tuning.

Records your voice reading prompts for XTTS-v2 fine-tuning.
Creates WAV files + transcript.txt ready for training.

Requirements:
    pip install sounddevice soundfile

Usage:
    python scripts/tts_finetuning/record_voice.py

Output:
    scripts/tts_finetuning/recordings/
        001.wav, 002.wav, ...
        transcript.txt
"""

import os
import sys
import time
from pathlib import Path

# Check dependencies
try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sounddevice", "soundfile"])
    import sounddevice as sd
    import soundfile as sf

# Configuration
SAMPLE_RATE = 22050  # XTTS-v2 preferred rate
CHANNELS = 1  # Mono
OUTPUT_DIR = Path(__file__).parent / "recordings"

# Prompts to read - mix of phonemes, emotions, and natural speech
PROMPTS = [
    # Basic sentences (warm up)
    "Hello, my name is Paul and I'm recording my voice for a custom assistant.",
    "The quick brown fox jumps over the lazy dog.",
    "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",

    # Numbers and dates
    "Today is December 28th, 2025. The time is 3:45 PM.",
    "Please call me at 555-123-4567 between 9 AM and 5 PM.",
    "The total comes to $1,234.56 including tax.",

    # Questions (rising intonation)
    "Would you like me to help you with that?",
    "What time would you like to schedule the appointment?",
    "Is there anything else I can assist you with today?",

    # Statements (neutral)
    "I understand. Let me look that up for you right away.",
    "Your appointment has been confirmed for next Tuesday.",
    "I'll send you an email with all the details.",

    # Empathy and emotion
    "I'm sorry to hear you're having trouble with that.",
    "That's wonderful news! Congratulations!",
    "I completely understand your frustration.",

    # Technical/professional
    "The server is currently undergoing scheduled maintenance.",
    "Your password has been successfully reset.",
    "The file has been uploaded to your cloud storage.",

    # Conversational
    "Sure, no problem at all.",
    "Let me think about that for a moment.",
    "Actually, I have a better idea.",

    # Longer passages
    "Welcome to the voice assistant. I'm here to help you with scheduling, "
    "reminders, and general questions. Just speak naturally and I'll do my best "
    "to understand and assist you.",

    "Thank you for your patience while I process your request. This may take "
    "a few moments. In the meantime, is there anything else you'd like to know?",

    # Edge cases (contractions, abbreviations)
    "I'll be there at 8 o'clock. Don't worry, I won't be late.",
    "You've got three new messages. They're all from Dr. Smith.",
    "It's raining outside, so you'll want to bring an umbrella.",

    # Commands the assistant might say
    "Playing your favorite playlist now.",
    "Setting a timer for fifteen minutes.",
    "Turning off the living room lights.",
    "Adding milk and eggs to your shopping list.",

    # More natural speech
    "Hmm, let me check on that for you.",
    "Oh, I see what you mean now.",
    "Right, so basically what happened was...",
    "Okay, got it. Moving on to the next item.",
]


def record_audio(duration_seconds: float = 10.0) -> tuple:
    """Record audio from microphone.

    Returns:
        Tuple of (audio_data, sample_rate)
    """
    print(f"\n  Recording for up to {duration_seconds} seconds...")
    print("  Press ENTER when done speaking (or wait for timeout)")

    # Start recording
    recording = sd.rec(
        int(duration_seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='float32'
    )

    # Wait for user to press enter or timeout
    import threading
    stop_event = threading.Event()

    def wait_for_enter():
        input()
        stop_event.set()
        sd.stop()

    thread = threading.Thread(target=wait_for_enter, daemon=True)
    thread.start()

    # Wait for recording to finish or user to press enter
    start_time = time.time()
    while not stop_event.is_set() and (time.time() - start_time) < duration_seconds:
        time.sleep(0.1)

    sd.stop()

    # Trim silence from end
    elapsed = time.time() - start_time
    samples_recorded = int(min(elapsed, duration_seconds) * SAMPLE_RATE)
    audio = recording[:samples_recorded]

    return audio, SAMPLE_RATE


def main():
    """Main recording session."""
    print("=" * 60)
    print("Voice Recording for TTS Fine-Tuning")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"Sample rate: {SAMPLE_RATE} Hz")
    print(f"Total prompts: {len(PROMPTS)}")
    print("\nInstructions:")
    print("  1. Read each prompt clearly and naturally")
    print("  2. Press ENTER when done speaking")
    print("  3. Type 'r' to re-record the last prompt")
    print("  4. Type 'q' to quit and save progress")
    print("  5. Type 's' to skip a prompt")
    print("\nTips:")
    print("  - Speak at your normal pace")
    print("  - Keep consistent distance from mic (~6 inches)")
    print("  - Record in a quiet room")
    print("  - Match the emotion/tone suggested by the text")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check for existing recordings
    existing = list(OUTPUT_DIR.glob("*.wav"))
    start_index = len(existing)

    if start_index > 0:
        print(f"\nFound {start_index} existing recordings.")
        resume = input("Continue from where you left off? (y/n): ").strip().lower()
        if resume != 'y':
            start_index = 0
            # Clear existing
            for f in existing:
                f.unlink()

    # Transcript file
    transcript_path = OUTPUT_DIR / "transcript.txt"
    transcript_mode = 'a' if start_index > 0 else 'w'

    print("\n" + "=" * 60)
    print("Starting recording session...")
    print("=" * 60)

    input("\nPress ENTER to begin...")

    recordings = []

    with open(transcript_path, transcript_mode, encoding='utf-8') as transcript_file:
        i = start_index
        while i < len(PROMPTS):
            prompt = PROMPTS[i]
            file_num = i + 1
            filename = f"{file_num:03d}.wav"
            filepath = OUTPUT_DIR / filename

            print(f"\n[{file_num}/{len(PROMPTS)}] Read this:")
            print("-" * 40)
            print(f"  \"{prompt}\"")
            print("-" * 40)

            # Record
            audio, sr = record_audio(duration_seconds=15.0)

            # Preview
            print(f"  Recorded {len(audio) / sr:.1f} seconds")

            # Ask what to do
            action = input("  Save (ENTER), re-record (r), skip (s), quit (q): ").strip().lower()

            if action == 'q':
                print("\nQuitting... Progress saved.")
                break
            elif action == 'r':
                print("  Re-recording...")
                continue  # Don't increment i
            elif action == 's':
                print("  Skipped.")
                i += 1
                continue
            else:
                # Save audio
                sf.write(filepath, audio, sr)

                # Save transcript line
                transcript_file.write(f"{filename}|{prompt}\n")
                transcript_file.flush()

                recordings.append((filename, prompt))
                print(f"  Saved: {filename}")
                i += 1

    # Summary
    print("\n" + "=" * 60)
    print("Recording Session Complete!")
    print("=" * 60)

    total_files = len(list(OUTPUT_DIR.glob("*.wav")))
    print(f"\nTotal recordings: {total_files}/{len(PROMPTS)}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Transcript: {transcript_path}")

    if total_files >= 20:
        print("\nYou have enough samples for basic fine-tuning!")
        print("For best results, aim for 50+ samples (~30 min of audio)")
    else:
        remaining = 20 - total_files
        print(f"\nRecord {remaining} more samples for minimum fine-tuning.")

    print("\nNext steps:")
    print("  1. Review recordings for quality")
    print("  2. Run: python scripts/tts_finetuning/prepare_dataset.py")
    print("  3. Upload to RunPod for training")


if __name__ == "__main__":
    main()
