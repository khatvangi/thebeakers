#!/usr/bin/env python3
"""generate podcast audio from transcript using dia tts"""

import sys
sys.path.insert(0, '/storage/dia')

import torch
import soundfile as sf
from dia.model import Dia

def main():
    # load transcript
    with open('/storage/thebeakers/kusumegi_podcast_transcript.txt', 'r') as f:
        transcript = f.read()

    print("Loading Dia model...")
    model = Dia.from_pretrained("nari-labs/Dia-1.6B-0626", compute_dtype="float16")

    print(f"Transcript length: {len(transcript)} chars")
    print("Generating audio (this may take a few minutes)...")

    # generate audio
    output = model.generate(
        transcript,
        max_tokens=3072,
        cfg_scale=3.0,
        temperature=1.3,
        top_p=0.95,
    )

    # save as wav
    output_path = '/storage/thebeakers/kusumegi_podcast.wav'
    sf.write(output_path, output, 44100)
    print(f"Audio saved to: {output_path}")

    # get duration
    duration = len(output) / 44100
    print(f"Duration: {duration:.1f} seconds")

if __name__ == "__main__":
    main()
