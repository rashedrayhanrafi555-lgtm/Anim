import numpy as np, wave, subprocess, imageio_ffmpeg

SR = 44100
DUR = 48.0
N = int(SR * DUR)
t = np.arange(N) / SR
mix = np.zeros(N)

def midi_f(m):
    return 440.0 * 2 ** ((m - 69) / 12)

def add_pad(freqs, t0, t1, amp=0.11):
    i0, i1 = int(t0 * SR), min(int(t1 * SR), N)
    n = i1 - i0
    tt = np.arange(n) / SR
    seg = np.zeros(n)
    for f in freqs:
        for det in (0.9985, 1.0015):
            seg += 0.5 * np.sin(2 * np.pi * f * det * tt + np.random.rand() * 6.28)
    seg += 0.22 * np.sin(2 * np.pi * freqs[0] / 2 * tt)
    env = np.ones(n)
    atk, rel = int(1.8 * SR), int(2.2 * SR)
    env[:atk] = np.linspace(0, 1, atk) ** 1.5
    env[-rel:] *= np.linspace(1, 0, rel) ** 1.2
    mix[i0:i1] += amp * seg * env / max(len(freqs), 1)

def add_pluck(freq, t0, amp=0.055, dur=1.4):
    i0 = int(t0 * SR)
    n = min(int(dur * SR), N - i0)
    tt = np.arange(n) / SR
    env = np.exp(-tt * 4.2) * (1 - np.exp(-tt * 60))
    mix[i0:i0 + n] += amp * env * (np.sin(2 * np.pi * freq * tt)
                                   + 0.35 * np.sin(2 * np.pi * freq * 2 * tt))

prog = [
    [48, 52, 55, 59],
    [40, 47, 52, 55],
    [41, 48, 53, 57],
    [43, 50, 55, 59],
]
arps = {0: [72, 76, 79, 83], 1: [76, 79, 83, 88], 2: [69, 72, 77, 81], 3: [71, 74, 79, 83]}
chord_len = 6.0
for cyc in range(2):
    for ci, chord in enumerate(prog):
        t0 = cyc * 24 + ci * chord_len
        add_pad([midi_f(m) for m in chord], t0, t0 + chord_len + 1.5)
        root = midi_f(chord[0] - 12)
        i0 = int(t0 * SR)
        seg = 0.05 * np.sin(2 * np.pi * root * np.arange(int(chord_len * SR)) / SR)
        seg *= np.minimum(1, np.arange(int(chord_len * SR)) / (0.5 * SR))
        mix[i0:i0 + len(seg)] += seg
        for k in range(4):
            add_pluck(midi_f(arps[ci][k]), t0 + k * 1.5 + 0.1)
        for k in range(4):
            add_pluck(midi_f(arps[ci][k]) * 2, t0 + 2.0 + k * 1.1, amp=0.028, dur=0.9)

wind = np.random.randn(N)
for _ in range(4):
    wind = np.convolve(wind, np.ones(2201) / 2201, mode="same")
mix += 0.9 * wind[:N]

fade = int(1.5 * SR)
mix[:fade] *= np.linspace(0, 1, fade)
mix[-fade:] *= np.linspace(1, 0, fade)
mix *= 0.85 / max(1e-9, np.max(np.abs(mix)))

st = np.zeros((N, 2))
st[:, 0] = mix
st[2200:, 1] = mix[:-2200]
st_int = (st * 32767).astype(np.int16)
with wave.open("mountain-boy/music_raw.wav", "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(st_int.tobytes())

subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                "-i", "mountain-boy/music_raw.wav", "-codec:a", "libmp3lame",
                "-qscale:a", "4", "mountain-boy/music.mp3"], check=True)
import os
os.remove("mountain-boy/music_raw.wav")
print("music.mp3", os.path.getsize("mountain-boy/music.mp3") // 1024, "KB")
