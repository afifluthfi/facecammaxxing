# AND-LC Video Kit

Gaya edit video training **AND Learning & Coaching**: animasi berkelas yang berganti paling lambat tiap ~3 detik,
subtitle otomatis dengan transisi, watermark `www.and-lc.com`, lower third pembicara, kartu poin, kutipan, ikon 3D,
B-roll, dan pemotongan jeda bicara. Dibangun di atas [facecammaxxing](../README.md) (Remotion + GSAP + Three.js).

## Isi kit

| File | Fungsi |
|---|---|
| `andlc.py` | Satu perintah untuk semua langkah: `prep`, `cut`, `plan`, `check`, `render` |
| `brand.json` | Gaya rumah: teks watermark, nama & jabatan lower third, kata yang disorot emas di subtitle |
| `fonts/` | Font yang dipakai (lisensi OFL), disalin otomatis ke folder kerja |
| `scripts/asr.py` | Transkrip Bahasa Indonesia (Whisper turbo, jalan offline di komputer sendiri) |
| `../remotion/src/effects/andlc.tsx` | Efek khas AND-LC: `sub`, `footer`, `lower`, `point`, `quote`, `broll` |
| `examples/memahami-kekuatan-diri/` | Contoh lengkap dari video "Memahami Kekuatan Diri" (beats, B-roll, transkrip) |

## Cara pakai paling mudah: lewat Claude Code

Buka repo ini di Claude Code (aplikasi desktop, web claude.ai/code, atau terminal) lalu kirim video dan minta:

> Edit video ini dengan gaya AND-LC: potong jeda (sedang), tambah B-roll, lower third untuk <nama, jabatan>.

Claude akan mengikuti panduan di `.claude/skills/andlc-video/SKILL.md`: menyiapkan video, menulis beat plan,
memeriksa stills, merender, lalu mengirim hasilnya.

## Instalasi sekali per komputer (kalau mau jalan di komputer sendiri)

Butuh: **Linux atau macOS** (di Windows pakai **WSL2 Ubuntu**), Git, ffmpeg, Node.js 22+, `uv`, `curl`.

```bash
git clone https://github.com/afifluthfi/facecammaxxing
cd facecammaxxing
git checkout andlc-training-kit
python3 scripts/fcm.py setup        # sampai muncul READY (venv Python, model, Remotion)
```

Model transkrip (~1,6 GB) diunduh otomatis ke `andlc/models-asr/` saat pertama kali `prep`.

## Alur kerja per video

```bash
K=".venv/bin/python andlc/andlc.py"

# 1. Siapkan: cut-out orang, pelacakan wajah, font, transkrip  -> folder kerja video_facecam/
$K prep "Memahami Kekuatan Diri.mp4" kerja/mkd

# 2. Koreksi teks transkrip di kerja/mkd/transcript.json (nama, istilah) — subtitle diambil dari sini.

# 3. Potong jeda (ringan | sedang | agresif)                    -> kerja/mkd_cut/
$K cut kerja/mkd --level sedang

# 4. Tulis beats.json (dan broll.json kalau ada B-roll), lalu susun plan
$K plan kerja/mkd --beats beats.json --broll broll.json --cut     # -> kerja/mkd_cut/plan.json

# 5. Cek stills dulu (lihat kerja/mkd_cut/check/plan/sheet.jpg)
$K check kerja/mkd_cut kerja/mkd_cut/plan.json --at 5,60,120,240

# 6. Render penuh + salinan kecil untuk dibagikan (*_share.mp4)
$K render kerja/mkd_cut kerja/mkd_cut/plan.json --out hasil/mkd.mp4
```

Semua waktu di `beats.json` dan `broll.json` memakai **detik video asli** (sebelum jeda dipotong); `--cut`
memindahkannya otomatis ke timeline yang sudah dipotong.

### Tingkat potong jeda

| Level | Jeda yang dipotong | Napas yang disisakan |
|---|---|---|
| `ringan` | > 0,6 dtk | ~0,4 dtk |
| `sedang` (standar) | > 0,35 dtk | ~0,25 dtk |
| `agresif` | > 0,25 dtk | ~0,16 dtk |

## Menulis beats.json

Satu efek per kalimat penting. Contoh lengkap ada di `examples/memahami-kekuatan-diri/beats.json`.

```json
[
  {"fx": "quote", "start": 1.0, "end": 5.3, "text": "Memahami *Kekuatan* & *Kelemahan* Diri", "size": 8.5},
  {"fx": "text-behind", "start": 10.5, "end": 13.9, "text": "KEKUATAN", "height": 125},
  {"fx": "point", "start": 14.5, "end": 21.5, "title": "Kuat dalam analitis",
   "items": "Melihat angka|Cepat menemukan pola", "at": ["melihat@17.9", "cepat@17.9"], "side": "right"},
  {"fx": "prop-3d", "start": 37.6, "end": 40.5, "model": "trophy", "size": 165, "light": "left", "side": "right"},
  {"fx": "spotlight", "start": 41.0, "end": 45.7, "push": 1.05},
  {"fx": "grade", "start": 111.5, "end": 124.3, "grade": "moody"}
]
```

| Efek | Kapan dipakai |
|---|---|
| `quote` | Judul / kalimat kunci di tengah layar, kata dalam `*bintang*` berwarna emas |
| `text-behind` | Satu kata besar yang muncul dari balik badan pembicara |
| `point` | Kartu poin di samping kepala; tiap item muncul pada waktunya (`at`: detik atau `"kata@detik"`) |
| `prop-3d` | Ikon 3D: `trophy`, `clock` (+`hours`), `check`, `x`, `coin`, `phone` |
| `spotlight` | Lampu meredup, pembicara tetap terang — untuk kalimat reflektif |
| `grade` | Nuansa warna sementara: `moody`, `cool`, `warm`, `bw`, `pop` |

Kamera (push & punch-in), subtitle, watermark dan lower third dibuat otomatis oleh `plan` — tidak perlu ditulis.

## B-roll

`broll.json` berisi daftar klip (path relatif terhadap file JSON itu):

```json
[{"file": "broll/analytics.mp4", "start": 14.6, "end": 19.6}]
```

Klip tampil penuh layar ±5 detik dengan bingkai garis emas; kartu poin yang tertutup otomatis digeser atau dibuang.
B-roll AI (mis. dari Tella / generator video lain) **bukan rekaman asli** — beri tahu klien bila perlu.

## Mengganti gaya rumah

Edit `brand.json` — misalnya pembicara lain:

```json
"lower_third": {"name": "Nama Lengkap, Gelar", "role": "Jabatan", "start": 0.4, "end": 9.3}
```

Warna emas (`#E9B85C`) dan tata letak efek ada di `remotion/src/effects/andlc.tsx`.

## Catatan

- Render 7 menit video butuh ±1–3 jam tergantung komputer (lebih cepat dengan GPU). Pakai `check` dulu.
- Selalu tonton hasil sampai selesai sebelum dibagikan, terutama sambungan potongan jeda.
- Kredit: facecammaxxing (aaksa) & claude-video-effects (Vibha Ramprakash, MIT). Remotion gratis untuk tim ≤ 3 orang;
  tim yang lebih besar perlu lisensi perusahaan Remotion.
