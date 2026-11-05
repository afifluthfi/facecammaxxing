---
name: andlc-video
description: Edit an AND Learning & Coaching (AND-LC) training / learning-snack talking-head video in the house style - classy animations that change at least every ~3 s, automatic Indonesian subtitles with transitions, the www.and-lc.com footer watermark, a lower third for the speaker in the first 10 s, point cards, quotes, 3D icons, B-roll cutaways and pause cutting. Use whenever someone on the AND-LC team asks to edit a training video, "edit video AND-LC", "potong jeda", "tambah B-roll", "subtitle otomatis", "lower third", or names the AND-LC style.
---

# AND-LC video

The house style is a kit on top of facecammaxxing (this repo). Read `andlc/README.md` first; for effect rules read
`SKILL.md`, `docs/director.md` and `docs/motion-rules.md` at the repo root. Talk to the user in Indonesian.

`K=".venv/bin/python andlc/andlc.py"` (run `python3 scripts/fcm.py setup` once if `.venv` is missing).
On a machine without a GPU the kit renders with `FCM_GL=swangle`; if Remotion cannot download Chrome, set
`FCM_BROWSER` to a local Chrome / chrome-headless-shell.

## Workflow

1. **Brief** - ask only what is missing: the speaker's name and title for the lower third (default in `andlc/brand.json`),
   pause cut level (`ringan` / `sedang` / `agresif`, default `sedang`), whether B-roll is wanted and from where.
2. **Prep** - `$K prep <video> <job>`: cut-out, face track, fonts, transcript (`<job>/transcript.json`). Read the
   transcript as a script and fix misheard names / terms in its `text` fields (subtitles come from it).
3. **Cut pauses** - `$K cut <job> --level sedang` -> `<job>_cut/` and `<job>/cuts.json`.
4. **Beats** - write `beats.json` in original-video seconds: one idea per important sentence (quote, text-behind,
   point with `at` items as `"word@seconds"`, prop-3d, spotlight, grade). Follow
   `andlc/examples/memahami-kekuatan-diri/beats.json` for density (~1 beat per 7-8 s) and tone. Never invent
   numbers or claims the speaker did not say.
5. **B-roll** (optional) - `broll.json` `[{"file": "broll/x.mp4", "start": s, "end": e}]`, one clip per concrete
   picture in the speech (~5 s each, about one per 35 s). AI-generated B-roll must be disclosed to the user as not real
   footage of the client.
6. **Plan** - `$K plan <job> --beats beats.json [--broll broll.json] --cut` -> `<job>_cut/plan.json`. It adds the
   camera rhythm (shot changes at least every ~3.3 s), subtitles, footer and lower third.
7. **Check** - `$K check <job>_cut <job>_cut/plan.json --at <6-10 times>` and LOOK at the contact sheet: no card over
   the face, subtitles readable, B-roll full frame, lower third in the first 10 s. Fix, check again.
8. **Render** - `$K render <job>_cut <job>_cut/plan.json --out <name>.mp4` (long: ~2.5x real time on 4 CPUs; run it in
   the background). Then probe duration/audio, make a contact sheet, and deliver `<name>_share.mp4` with a short
   Indonesian note: what was done, how much pause time was removed, what is AI-generated, and a reminder to watch it
   in full before distributing.
