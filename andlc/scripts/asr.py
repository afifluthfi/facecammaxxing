#!/usr/bin/env python3
"""Indonesian transcript with approximate word times, via sherpa-onnx Whisper (turbo) + Silero VAD.
usage: asr.py <video> <model-dir> <vad.onnx> <out.json>
Word times are spread across each speech segment by character length (Whisper in sherpa-onnx gives no word stamps)."""
import json, subprocess, sys
import numpy as np
import sherpa_onnx

video, mdir, vad_path, out = sys.argv[1:5]
SR = 16000
pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                     capture_output=True, check=True).stdout
audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

import glob, os
enc = glob.glob(os.path.join(mdir, '*encoder*int8*.onnx')) or glob.glob(os.path.join(mdir, '*encoder*.onnx'))
dec = glob.glob(os.path.join(mdir, '*decoder*int8*.onnx')) or glob.glob(os.path.join(mdir, '*decoder*.onnx'))
tok = glob.glob(os.path.join(mdir, '*tokens.txt'))
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=enc[0], decoder=dec[0], tokens=tok[0], language='id',
                                                 task='transcribe', num_threads=4)

cfg = sherpa_onnx.VadModelConfig()
cfg.silero_vad.model = vad_path
cfg.silero_vad.min_silence_duration = 0.35
cfg.silero_vad.min_speech_duration = 0.25
cfg.silero_vad.max_speech_duration = 12
cfg.sample_rate = SR
vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)
win = cfg.silero_vad.window_size
segs = []
for i in range(0, len(audio), win):
    vad.accept_waveform(audio[i:i + win])
    while not vad.empty():
        segs.append((vad.front.start, np.array(vad.front.samples))); vad.pop()
vad.flush()
while not vad.empty():
    segs.append((vad.front.start, np.array(vad.front.samples))); vad.pop()

result = []
for n, (start, samples) in enumerate(segs):
    s = rec.create_stream(); s.accept_waveform(SR, samples); rec.decode_stream(s)
    text = s.result.text.strip()
    t0, t1 = start / SR, (start + len(samples)) / SR
    words = text.split()
    if not words: continue
    total = sum(len(w) + 1 for w in words); acc = 0
    ws = []
    for w in words:
        a = t0 + (t1 - t0) * acc / total; acc += len(w) + 1
        ws.append({'w': w, 's': round(a, 2), 'e': round(t0 + (t1 - t0) * acc / total, 2)})
    result.append({'s': round(t0, 2), 'e': round(t1, 2), 'text': text, 'words': ws})
    print(f'{t0:7.2f}-{t1:7.2f}  {text}', flush=True)
json.dump(result, open(out, 'w'), ensure_ascii=False, indent=1)
print(f'saved {len(result)} segments')
