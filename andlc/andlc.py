#!/usr/bin/env python3
"""AND-LC video kit: the house style for AND Learning & Coaching training videos, on top of facecammaxxing.

  andlc.py prep   <video> [<job>]                       cut-out + face track + fonts + Indonesian transcript
  andlc.py cut    <job> [--level ringan|sedang|agresif] shorten the pauses -> <job>_cut (+ <job>/cuts.json)
  andlc.py plan   <job> --beats beats.json [--broll broll.json] [--cut] [--out plan.json]
                                                        subtitles + camera every ~3 s + beats + B-roll + footer + lower third
  andlc.py check  <job> <plan.json> --at 5,60,120       stills + contact sheet before the long render
  andlc.py render <job> <plan.json> [--out final.mp4]   full render, then a compressed copy for sharing (*_share.mp4)

Times in beats.json and broll.json are seconds of the ORIGINAL (uncut) video; `plan --cut` moves them onto the cut take.
House style (watermark, lower third, gold words) lives in andlc/brand.json.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys

KIT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(KIT)
PY = os.path.join(ROOT, '.venv', 'bin', 'python')
FCM = os.path.join(ROOT, 'scripts', 'fcm.py')
ASR_DIR = os.path.join(KIT, 'models-asr')
LEVELS = {  # silence threshold dB, min pause s, breath kept before / after
    'ringan': (-32, 0.60, 0.20, 0.20),
    'sedang': (-30, 0.35, 0.12, 0.13),
    'agresif': (-28, 0.25, 0.08, 0.08),
}


def run(cmd, **kw):
    print('$', ' '.join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True, **kw)


def fps_of(job):
    t = json.load(open(os.path.join(job, 'track.json')))
    return t.get('fps', 30), t


def brand():
    return json.load(open(os.path.join(KIT, 'brand.json'), encoding='utf8'))


# ---------------------------------------------------------------- prep
def asr_models():
    turbo = os.path.join(ASR_DIR, 'sherpa-onnx-whisper-turbo')
    vad = os.path.join(ASR_DIR, 'silero_vad.onnx')
    base = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models'
    os.makedirs(ASR_DIR, exist_ok=True)
    if not os.path.isdir(turbo):
        tar = os.path.join(ASR_DIR, 'turbo.tar.bz2')
        run(['curl', '-L', '-o', tar, f'{base}/sherpa-onnx-whisper-turbo.tar.bz2'])
        run(['tar', 'xjf', tar, '-C', ASR_DIR]); os.remove(tar)
    if not os.path.exists(vad):
        run(['curl', '-L', '-o', vad, f'{base}/silero_vad.onnx'])
    try:
        subprocess.run([PY, '-c', 'import sherpa_onnx'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        run(['uv', 'pip', 'install', '-p', PY, 'sherpa-onnx', 'soundfile'])
    return turbo, vad


def prep(a):
    job = a.job or os.path.splitext(a.video)[0] + '_facecam'
    if not os.path.exists(os.path.join(job, 'track.json')):
        run([PY, FCM, 'track', a.video, job] + (['--width', str(a.width)] if a.width else []))
    os.makedirs(os.path.join(job, 'fonts'), exist_ok=True)
    for f in glob.glob(os.path.join(KIT, 'fonts', '*.woff2')): shutil.copy(f, os.path.join(job, 'fonts'))
    tr = os.path.join(job, 'transcript.json')
    if not os.path.exists(tr):
        turbo, vad = asr_models()
        run([PY, os.path.join(KIT, 'scripts', 'asr.py'), os.path.join(job, 'source.mp4'), turbo, vad, tr])
    print(f'\nSiap: {job}\nPeriksa & koreksi teks di {tr} (field "text"), lalu tulis beats.json.')


# ---------------------------------------------------------------- cut
def cut(a):
    job = a.job.rstrip('/'); out = a.out or job + '_cut'
    fps, track = fps_of(job)
    n = track['frames']
    db, dmin, pre, post = LEVELS[a.level]
    log = subprocess.run(['ffmpeg', '-v', 'info', '-i', os.path.join(job, 'source.mp4'), '-vn', '-af',
                          f'silencedetect=noise={db}dB:d={dmin}', '-f', 'null', '-'], capture_output=True, text=True).stderr
    gaps = [(float(e) - float(d), float(e)) for e, d in re.findall(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)', log)]
    rm = []
    for s, e in gaps:
        x0 = s + pre if s > 0.05 else 0.0
        x1 = e - post
        if x1 >= n / fps - 0.05: x1 = n / fps; x0 = s + 0.9          # keep a soft tail at the end
        if x1 - x0 >= 0.1: rm.append((round(x0 * fps), round(x1 * fps)))
    keep, cur = [], 0
    for x0, x1 in rm:
        if x0 > cur: keep.append((cur, x0))
        cur = max(cur, x1)
    if cur < n: keep.append((cur, n))
    kept = sum(b - a_ for a_, b in keep)
    json.dump({'keep': keep, 'fps': fps, 'level': a.level}, open(os.path.join(job, 'cuts.json'), 'w'))
    print(f'{len(rm)} jeda dipotong; {n / fps:.1f}s -> {kept / fps:.1f}s (hemat {(n - kept) / fps:.1f}s)')

    os.makedirs(out, exist_ok=True)
    sel = '+'.join(f'between(n,{x0},{x1 - 1})' for x0, x1 in keep)
    open(os.path.join(out, 'vsel.txt'), 'w').write(f"select='{sel}',setpts=N/{fps}/TB")
    parts = []
    for i, (x0, x1) in enumerate(keep):
        s, e = x0 / fps, x1 / fps; d = e - s
        parts.append(f'[0:a]atrim={s:.5f}:{e:.5f},asetpts=PTS-STARTPTS,afade=t=in:d=0.006,'
                     f'afade=t=out:st={max(0, d - 0.006):.5f}:d=0.006[a{i}]')
    open(os.path.join(out, 'afilt.txt'), 'w').write(';\n'.join(parts) + ';\n' + ''.join(f'[a{i}]' for i in range(len(keep)))
                                                    + f'concat=n={len(keep)}:v=0:a=1[aout]')
    idx = [i for x0, x1 in keep for i in range(x0, x1)]
    t = dict(track); t['face'] = [track['face'][i] for i in idx]; t['top'] = [track['top'][i] for i in idx]
    t['frames'] = len(idx); t['duration'] = len(idx) / fps
    json.dump(t, open(os.path.join(out, 'track.json'), 'w'))
    for f in ['plate.jpg', 'transcript.json']:
        if os.path.exists(os.path.join(job, f)): shutil.copy(os.path.join(job, f), out)
    for d in ['fonts', 'models']:
        if os.path.isdir(os.path.join(job, d)): shutil.copytree(os.path.join(job, d), os.path.join(out, d), dirs_exist_ok=True)
    vs, af = os.path.join(out, 'vsel.txt'), os.path.join(out, 'afilt.txt')
    jobs = [['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(job, 'source.mp4'), '-filter_script:v', vs,
             '-filter_complex_script', af, '-map', '0:v', '-map', '[aout]', '-c:v', 'libx264', '-crf', '14', '-preset', 'medium',
             '-g', '15', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
             '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', os.path.join(out, 'source.mp4')]]
    if os.path.exists(os.path.join(job, 'room.mp4')):
        jobs.append(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(job, 'room.mp4'), '-filter_script:v', vs, '-c:v', 'libx264',
                     '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-an', os.path.join(out, 'room.mp4')])
    jobs.append(['ffmpeg', '-v', 'error', '-y', '-c:v', 'libvpx-vp9', '-i', os.path.join(job, 'person.webm'), '-filter_script:v', vs,
                 '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-auto-alt-ref', '0', '-b:v', '0', '-crf', '20',
                 '-deadline', 'realtime', '-cpu-used', '8', '-row-mt', '1', '-an', os.path.join(out, 'person.webm')])
    procs = [subprocess.Popen(j) for j in jobs]
    if any(p.wait() for p in procs): sys.exit('ffmpeg gagal saat memotong jeda')
    print(f'Siap: {out}')


# ---------------------------------------------------------------- plan
def plan(a):
    job = a.job.rstrip('/'); B = brand()
    fps, track = fps_of(job)
    DUR = track['duration']
    segs = [(float(s['s']), float(s['e']), s['text'].strip()) for s in json.load(open(os.path.join(job, 'transcript.json'), encoding='utf8'))
            if s['text'].strip()]

    words = []
    for i, (s, e, text) in enumerate(segs):
        ws = text.split(); total = sum(len(w) + 1 for w in ws); acc = 0
        for w in ws:
            t0 = s + (e - s) * acc / total; acc += len(w) + 1
            words.append((round(t0, 2), round(s + (e - s) * acc / total, 2), w, i))

    def W(word, after):
        key = word.lower()
        for t, _, w, _ in words:
            if t >= after - 0.05 and re.sub(r'[^\w-]', '', w.lower()).startswith(key): return t
        sys.exit(f'kata tidak ditemukan di transkrip: "{word}" setelah {after}s')

    def at_val(v):
        if isinstance(v, str) and '@' in v: w, t = v.split('@'); return W(w, float(t))
        return float(v)

    # subtitles
    GOLD = set(w.lower() for w in B.get('gold_words', [])); MAXC = B.get('subtitle_max_chars', 42)
    cues = []
    for i in range(len(segs)):
        ws = [x for x in words if x[3] == i]; chunk = []
        for k, x in enumerate(ws):
            chunk.append(x)
            line = ' '.join(y[2] for y in chunk)
            nxt = ws[k + 1][2] if k + 1 < len(ws) else ''
            if not nxt or len(line) + 1 + len(nxt) > MAXC or (re.search(r'[,.?:;]$', x[2]) and len(line) >= 16):
                cues.append(list(chunk)); chunk.clear()
    merged = []
    for cu in cues:
        tail = ' '.join(y[2] for y in cu)
        if merged and len(tail) <= 9 and merged[-1][-1][3] == cu[0][3] and len(' '.join(y[2] for y in merged[-1] + cu)) <= MAXC + 10:
            merged[-1] = merged[-1] + cu
        else: merged.append(cu)
    subs = []
    for j, cu in enumerate(merged):
        st = cu[0][0] - 0.06
        nxt = merged[j + 1][0][0] - 0.06 if j + 1 < len(merged) else DUR
        end = min(nxt, cu[-1][1] + 0.7) if nxt - cu[-1][1] > 0.05 else nxt
        used = False; toks = []
        for x in cu:
            if re.sub(r'[^\w]', '', x[2].lower()) in GOLD and not used:
                m = re.match(r'^(.*?)([.,?!:;]*)$', x[2]); toks.append(f'*{m.group(1)}*{m.group(2)}'); used = True
            else: toks.append(x[2])
        subs.append({'fx': 'sub', 'start': round(st, 2), 'end': round(max(end, st + 0.8), 2), 'text': ' '.join(toks),
                     'times': ','.join(f'{x[0]:.2f}' for x in cu)})

    # beats from the editor
    beats = json.load(open(a.beats, encoding='utf8')) if a.beats else []
    for b in beats:
        if 'at' in b:
            ats = b['at'] if isinstance(b['at'], list) else str(b['at']).split(',')
            b['at'] = ','.join(f'{at_val(v):.2f}' for v in ats)

    # camera: a push or a punch-in so the shot changes at least every ~3 s
    CAMS = []
    def push(s, e, z=1.1): CAMS.append({'fx': 'slow-push', 'start': round(s, 2), 'end': round(e, 2), 'zoom': z, 'blur': 2.5, 'parallax': 0.5})
    def punch(s, e, z=1.12): CAMS.append({'fx': 'lean-in', 'start': round(s, 2), 'end': round(e, 2), 'zoom': z, 'dof': 2.5, 'parallax': 0.35, 'in': 6, 'out': 8})
    busy = [(b['start'], b['end']) for b in beats if b['fx'] in ('spotlight',)]
    def free(s, e): return all(e <= x or s >= y for x, y in busy + [(c['start'], c['end']) for c in CAMS])
    k = 0
    for i, (s, e, _) in enumerate(segs):
        span_end = min((segs[i + 1][0] if i + 1 < len(segs) else DUR) - 0.05, DUR)
        if e - s >= 3.2 and free(s, span_end):
            if k % 2 == 0: push(s, span_end, 1.08 + 0.03 * ((k // 2) % 2))
            else:
                mid = s + (e - s) * 0.45
                if free(mid, span_end): punch(mid, span_end, 1.1 + 0.03 * ((k // 2) % 2))
            k += 1
        elif e - s >= 1.0 and free(s + 0.2, span_end) and k % 3 == 0:
            punch(s + 0.15, span_end, 1.12); k += 1
    word_starts = [w[0] for w in words]; LIM = B.get('max_still_seconds', 3.3)
    def changes():
        return sorted({0.0, DUR} | {x['start'] for x in CAMS + beats} | {x['end'] for x in CAMS + beats}
                      | {float(t) for b in beats for t in str(b.get('at', '')).split(',') if t})
    for _ in range(400):
        ch = changes()
        x0, x1 = max(zip(ch, ch[1:]), key=lambda ab: ab[1] - ab[0])
        if x1 - x0 <= LIM: break
        mid = x0 + (x1 - x0) / 2
        cand = [t for t in word_starts if x0 + 1.2 <= t <= x1 - 1.2]
        t = round((min(cand, key=lambda v: abs(v - mid)) if cand else mid) - 0.05, 2)
        cov = [c for c in CAMS if c['start'] < t < c['end']]
        if cov:
            c = cov[0]; old = c['end']; c['end'] = t
            (punch if c['fx'] == 'slow-push' else push)(t, old)
        else:
            punch(t, min([c['start'] for c in CAMS if c['start'] > t] + [x1 + 2.0, DUR, t + 2.6]))
    CAMS.sort(key=lambda c: c['start'])

    # B-roll: point cards it would cover move out of its way or go
    BR = json.load(open(a.broll, encoding='utf8')) if a.broll else []
    kept = []
    for b in beats:
        for r in BR:
            s0, e0 = r['start'], r['end']
            if b['fx'] == 'point' and b['start'] < e0 and b['end'] > s0:
                if b['start'] >= s0 - 0.5 and b['end'] - e0 > 2.8: b['start'] = round(e0 + 0.1, 2)
                elif b['start'] < s0 - 0.5 and s0 - b['start'] > 2.8: b['end'] = round(s0 - 0.1, 2)
                else: b['drop'] = True
        if not b.pop('drop', False): kept.append(b)
    beats = kept
    brolls = [{'fx': 'broll', 'start': r['start'], 'end': r['end'], 'src': r['file'], **({'from': r['from']} if 'from' in r else {})} for r in BR]

    lt = B['lower_third']
    effects = CAMS + beats + brolls + [
        {'fx': 'lower', 'start': lt['start'], 'end': lt['end'], 'name': lt['name'], 'role': lt['role']},
        {'fx': 'footer', 'start': 0, 'end': DUR, 'text': B['watermark']}] + subs
    for x in effects: x['end'] = min(x['end'], DUR)

    out_job = job
    if a.cut:
        cj = json.load(open(os.path.join(job, 'cuts.json'))); keep = cj['keep']; out_job = job + '_cut'
        offs, acc = [], 0
        for x0, x1 in keep: offs.append(acc); acc += x1 - x0
        def R(t):
            f = t * fps
            for (x0, x1), o in zip(keep, offs):
                if f < x0: return round(o / fps, 3)
                if f <= x1: return round((o + f - x0) / fps, 3)
            return round(acc / fps, 3)
        for x in effects:
            if x['fx'] == 'lower': continue
            x['start'], x['end'] = R(x['start']), R(x['end'])
            for key in ('times', 'at'):
                if x.get(key): x[key] = ','.join(f'{R(float(v)):.3f}' for v in str(x[key]).split(','))
    for x in effects:
        if x['fx'] == 'broll':
            x['rate'] = round(min(1.0, B.get('broll_max_seconds', 5.0) / max(0.1, x['end'] - x['start'])), 3)
            src = os.path.join(os.path.dirname(os.path.abspath(a.broll)), x['src'])
            dst = os.path.join(out_job, x['src'])
            if os.path.exists(src) and os.path.abspath(src) != os.path.abspath(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(src, dst)
            elif not os.path.exists(dst): print(f'PERINGATAN: file B-roll tidak ada: {src}')
    effects = [x for x in effects if x['end'] - x['start'] > 0.2]
    out = a.out or os.path.join(out_job, 'plan.json')
    json.dump({'effects': effects}, open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    print(f'{len(beats)} beat, {len(CAMS)} gerakan kamera, {len(brolls)} B-roll, {len(subs)} subtitle -> {out}')
    print(f'Render dari folder: {out_job}')


# ---------------------------------------------------------------- check / render
def env():
    e = dict(os.environ)
    if 'FCM_GL' not in e and not shutil.which('nvidia-smi'): e['FCM_GL'] = 'swangle'
    return e


def check(a):
    run([PY, FCM, 'check', a.job, a.plan] + (['--at', a.at] if a.at else []), env=env())


def render(a):
    out = a.out or os.path.join(a.job, 'final.mp4')
    run([PY, FCM, 'render', a.job, a.plan, '--out', out, '--concurrency', str(a.concurrency), '--crf', '18'], env=env())
    share = os.path.splitext(out)[0] + '_share.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-i', out, '-c:v', 'libx264', '-crf', '24', '-preset', 'medium', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', share])
    print(f'Selesai: {out}\nUntuk dibagikan: {share}')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest='cmd', required=True)
    x = sp.add_parser('prep'); x.add_argument('video'); x.add_argument('job', nargs='?'); x.add_argument('--width', type=int, default=1280, help='lebar kerja (1280 = 720p landscape)'); x.set_defaults(f=prep)
    x = sp.add_parser('cut'); x.add_argument('job'); x.add_argument('--level', default='sedang', choices=LEVELS); x.add_argument('--out'); x.set_defaults(f=cut)
    x = sp.add_parser('plan'); x.add_argument('job'); x.add_argument('--beats'); x.add_argument('--broll'); x.add_argument('--cut', action='store_true')
    x.add_argument('--out'); x.set_defaults(f=plan)
    x = sp.add_parser('check'); x.add_argument('job'); x.add_argument('plan'); x.add_argument('--at'); x.set_defaults(f=check)
    x = sp.add_parser('render'); x.add_argument('job'); x.add_argument('plan'); x.add_argument('--out'); x.add_argument('--concurrency', type=int, default=4)
    x.set_defaults(f=render)
    a = p.parse_args(); a.f(a)


if __name__ == '__main__':
    main()
