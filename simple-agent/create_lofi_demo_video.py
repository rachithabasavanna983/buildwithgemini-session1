import math
import os
import struct
import subprocess
import wave
from google.cloud import storage

FIRESTORE_PROJECT_ID = "qwiklabs-gcp-03-5ae45ab25a38"
GCS_BUCKET_NAME = "smart-pantry-images-qwiklabs-gcp-03-5ae45ab25a38"
ARTIFACT_DIR = "/config/.gemini/antigravity/brain/01320f7a-abec-4f79-8a24-15527b270f1c"


def generate_upbeat_lofi_wav(output_filename="lofi_beat.wav", duration_sec=10.0, sample_rate=44100):
    """Generates an upbeat lo-fi music track using pure Python math and wave synthesis."""
    num_samples = int(sample_rate * duration_sec)
    bpm = 90
    beat_sec = 60.0 / bpm
    step_sec = beat_sec / 4.0  # 16th note

    # Chord frequencies (Hz): Cmaj7, Am7, Dm7, G7 (lofi warm keys)
    chords = [
        [261.63, 329.63, 392.00, 493.88],  # Cmaj7
        [220.00, 261.63, 329.63, 392.00],  # Am7
        [146.83, 174.61, 220.00, 261.63],  # Dm7
        [196.00, 246.94, 293.66, 349.23],  # G7
    ]

    bass_notes = [130.81, 110.00, 73.42, 98.00]  # C3, A2, D2, G2

    frames = bytearray()
    import random
    rng = random.Random(42)

    for i in range(num_samples):
        t = i / sample_rate
        beat_idx = int(t / (beat_sec * 2)) % len(chords)
        chord = chords[beat_idx]
        bass_freq = bass_notes[beat_idx]

        step_in_bar = int(t / step_sec) % 16
        t_step = math.fmod(t, step_sec)

        # 1. Warm Lofi Keys
        tremolo = 1.0 + 0.15 * math.sin(2 * math.pi * 5.0 * t)
        keys_val = 0.0
        for freq in chord:
            sig = math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(2 * math.pi * freq * 2 * t)
            keys_val += sig
        keys_val *= 0.12 * tremolo

        # 2. Smooth Sub Bass
        bass_env = math.exp(-3.0 * (math.fmod(t, beat_sec) / beat_sec))
        bass_val = math.sin(2 * math.pi * bass_freq * t) * 0.25 * bass_env

        # 3. Upbeat Lofi Drums
        kick_val = 0.0
        snare_val = 0.0
        hihat_val = 0.0

        if step_in_bar in (0, 6, 8, 14):
            k_env = math.exp(-25.0 * t_step)
            k_freq = 120.0 * math.exp(-30.0 * t_step) + 40.0
            kick_val = math.sin(2 * math.pi * k_freq * t_step) * 0.4 * k_env

        if step_in_bar in (4, 12):
            s_env = math.exp(-20.0 * t_step)
            noise = (rng.random() * 2.0 - 1.0)
            snare_val = (0.5 * math.sin(2 * math.pi * 180.0 * t_step) + 0.5 * noise) * 0.3 * s_env

        if step_in_bar % 2 == 0:
            h_env = math.exp(-60.0 * t_step)
            h_noise = (rng.random() * 2.0 - 1.0)
            hihat_val = h_noise * 0.08 * h_env

        # 4. Vinyl Crackle
        crackle = 0.0
        if rng.random() < 0.008:
            crackle = (rng.random() * 2.0 - 1.0) * 0.05

        sample_float = max(-0.95, min(0.95, keys_val + bass_val + kick_val + snare_val + hihat_val + crackle))
        sample_int = int(sample_float * 32767)
        frames.extend(struct.pack("<h", sample_int))

    with wave.open(output_filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frames)

    print(f"Generated upbeat lofi WAV track: {output_filename} (10.0s)")
    return output_filename


def build_lofi_demo_video():
    # 1. Kill old task if running & generate audio track
    audio_path = "lofi_beat.wav"
    generate_upbeat_lofi_wav(output_filename=audio_path, duration_sec=10.0)

    raw_video = "fresh_organic_eggs_dc0089.mp4"
    if not os.path.exists(raw_video):
        gcs_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = gcs_client.bucket(GCS_BUCKET_NAME)
        blobs = list(bucket.list_blobs(prefix="fresh_organic_eggs"))
        if blobs:
            blobs[0].download_to_filename(raw_video)

    output_demo = "agent_demo_lofi.mp4"

    # Combine video with lo-fi audio track, exactly 10s duration
    cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop", "2",
        "-i", raw_video,
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", "10",
        output_demo
    ]
    subprocess.run(cmd, check=True)
    print(f"Successfully created upbeat lofi demo video: {output_demo}")

    # Save to Playground Artifacts panel
    artifact_dest = os.path.join(ARTIFACT_DIR, "agent_demo_lofi.mp4")
    with open(output_demo, "rb") as src, open(artifact_dest, "wb") as dst:
        dst.write(src.read())
    print(f"Saved artifact to Playground panel: {artifact_dest}")

    # Upload to GCS
    gcs_client = storage.Client(project=FIRESTORE_PROJECT_ID)
    bucket = gcs_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob("agent_demo_lofi.mp4")
    with open(output_demo, "rb") as f:
        blob.upload_from_file(f, content_type="video/mp4")

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/agent_demo_lofi.mp4"
    print(f"Public GCS URL: {public_url}")
    return public_url, artifact_dest

if __name__ == "__main__":
    url, artifact_path = build_lofi_demo_video()
    print("LOFI DEMO VIDEO COMPLETED!")
