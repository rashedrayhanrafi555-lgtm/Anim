import numpy as np, wave, subprocess, os, imageio_ffmpeg

SR = 44100
BPM = 132
BEAT = 60.0 / BPM
DUR = 26.0
N = int(SR * DUR)
mix = np.zeros(N)

def sq(ph, duty=0.25):
    return np.where((ph % 1.0) < duty, 1.0, -1.0)

def add_note(freq, t0, dur, amp=0.10, wave_kind="sq", duty=0.25):
    i0 = int(t0 * SR); n = min(int(dur * SR), N - i0)
    if n <= 0: return
    tt = np.arange(n) / SR
    ph = freq * tt + 0.002
    env = np.minimum(1, tt / (0.004 * SR * 0 + 0.005)) * np.exp(-tt * 6.0 / max(dur, 0.12))
    w = sq(ph, duty).astype(np.float64) if wave_kind == "sq" else np.tanh(2.2 * np.sin(2 * np.pi * ph))
    mix[i0:i0 + n] += amp * env * w

def add_hat(t0, amp=0.05):
    i0 = int(t0 * SR); n = min(int(0.06 * SR), N - i0)
    rng = np.random.default_rng(7)
    mix[i0:i0 + n] += amp * rng.standard_normal(n) * np.exp(-np.arange(n) / (0.012 * SR))

# C major pentatonic bouncy melody (8 semitones above C4)
def m(mn): return 440.0 * 2 ** ((mn - 69) / 12)
melody = [
    72, 0, 76, 72, 79, 0, 76, 0,
    74, 0, 77, 74, 81, 0, 77, 0,
    76, 0, 79, 76, 84, 0, 79, 76,
    77, 76, 74, 72, 74, 0, 0, 0,
]
bass_pat = [48, 48, 55, 48, 52, 52, 59, 52]
for bar in range(int(DUR / 2.0)):
    t0 = bar * 2.0
    for i, mnote in enumerate(melody):
        tt = t0 + i * (2.0 / 8)
        if mnote: add_note(m(mnote), tt, 1.8 * BEAT, amp=0.085, duty=0.3)
    for i in range(8):
        tt = t0 + i * (2.0 / 8)
        add_note(m(bass_pat[i % 8] - 12), tt, 1.2 * BEAT, amp=0.16, wave_kind="tr")
    for i in range(8):
        if i % 2 == 1: add_hat(t0 + i * 0.25, amp=0.045)

fade = int(0.6 * SR)
mix[:fade] *= np.linspace(0, 1, fade)
mix[-fade:] *= np.linspace(1, 0, fade)
mix *= 0.8 / max(1e-9, np.max(np.abs(mix)))
st = (np.repeat(mix, 2).reshape(N, 2) * 32767).astype(np.int16)
with wave.open("roblox-short/music8bit.wav", "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(st.tobytes())
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                "-i", "roblox-short/music8bit.wav", "-codec:a", "libmp3lame", "-qscale:a", "4",
                "roblox-short/music8bit.mp3"], check=True)
os.remove("roblox-short/music8bit.wav")
print("music8bit.mp3", os.path.getsize("roblox-short/music8bit.mp3") // 1024, "KB")
