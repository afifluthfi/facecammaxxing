import React from 'react';
import { AbsoluteFill, OffthreadVideo, Sequence, staticFile } from 'remotion';
import { clamp, e, FxCtx, FxDef, lerp, list, opt, str } from '../lib/core';
import { FONT } from '../lib/fonts';

// A training-video kit for landscape learning snacks: subtitles that land word by word, a footer watermark, a lower
// third, and smoked-glass point cards beside the head. Sizes are written against the frame height (u = 1 % of H), so they
// read the same at 720p and 1080p. Same motion rules as the rest of the library: entries do their travel in the first
// ~6 frames and focus up from a blur, exits ease in, holds keep a slow drift.

export const GOLD = '#E9B85C';
const u = (c: FxCtx, v: number) => (v * c.H) / 100;
const glass = (c: FxCtx): React.CSSProperties => ({
  background: 'linear-gradient(160deg, rgba(22,24,30,0.62), rgba(14,15,19,0.5))',
  border: '1px solid rgba(255,255,255,0.18)', borderRadius: u(c, 1.6),
  backdropFilter: 'blur(18px) saturate(140%)', WebkitBackdropFilter: 'blur(18px) saturate(140%)',
  boxShadow: `0 ${u(c, 2.2)}px ${u(c, 5)}px rgba(0,0,0,0.32), inset 0 1px 0 rgba(255,255,255,0.1)`,
});

// ---------- subtitles ----------
// One cue: words in `text` (*starred* words in gold), `times` = clip second each word lands. Each word focuses up from a
// blur and a small rise ~2 frames before it is heard; the cue leaves by going soft and sinking a little.
const Sub: React.FC<{ c: FxCtx }> = ({ c }) => {
  const raw = str(c, 'text', '').split(/\s+/).filter(Boolean);
  const times = list(c, 'times', []).map(Number);
  const t = c.t + c.o.start;
  const out = e('power2.in', c.t, c.d - 0.16, 0.16);
  const fs = u(c, opt(c, 'size', 4.6));
  return (
    <AbsoluteFill>
      <div style={{
        position: 'absolute', left: c.W * 0.12, width: c.W * 0.76, bottom: u(c, opt(c, 'bottom', 9.5)), textAlign: 'center',
        fontFamily: FONT.ui, fontWeight: 600, fontSize: fs, lineHeight: 1.22, letterSpacing: '-0.01em', color: '#fff',
        textShadow: `0 ${u(c, 0.2)}px ${u(c, 1.2)}px rgba(0,0,0,0.75), 0 0 ${u(c, 3)}px rgba(0,0,0,0.35)`,
        transform: `translateY(${out * u(c, 1.2)}px)`, filter: out > 0.01 ? `blur(${out * u(c, 0.9)}px)` : undefined, opacity: 1 - out * 0.9,
      }}>
        {raw.map((w0, i) => {
          const gold = /^\*.*\*[.,?!:;]*$/.test(w0), w = w0.replace(/\*/g, '');
          const at = (times[i] ?? c.o.start) - 2 / 30;
          const k = e('expo.out', t, at, 7 / 30);
          return (
            <span key={i} style={{
              display: 'inline-block', whiteSpace: 'pre', color: gold ? GOLD : undefined,
              opacity: clamp(k * 2.5), transform: `translateY(${(1 - k) * fs * 0.32}px)`,
              filter: k < 0.98 ? `blur(${(1 - k) * fs * 0.16}px)` : undefined,
            }}>{w}{i < raw.length - 1 ? ' ' : ''}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
export const SUB: FxDef = {
  desc: 'One subtitle cue: words land one by one on the voice (focus up from a blur), *starred* words in gold',
  options: 'text, times (clip seconds per word), size (4.6 % of H), bottom (9.5 % of H)',
  Screen: Sub,
};

// ---------- footer: a soft dark floor and the watermark ----------
const Footer: React.FC<{ c: FxCtx }> = ({ c }) => {
  const k = e('power2.out', c.t, 0, 0.6);
  const fs = u(c, opt(c, 'size', 2.7));
  const sheen = ((c.t % 9) / 9);                     // a slow glint along the rule every 9 s: the footer's living thing
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: `linear-gradient(180deg, rgba(0,0,0,0) 62%, rgba(0,0,0,${0.42 * k}) 100%)` }} />
      <div style={{
        position: 'absolute', right: u(c, 3.2), bottom: u(c, 2.6), display: 'flex', alignItems: 'center', gap: u(c, 1.1),
        fontFamily: FONT.ui, fontWeight: 600, fontSize: fs, letterSpacing: '0.04em', color: 'rgba(255,255,255,0.86)',
        textShadow: '0 1px 6px rgba(0,0,0,0.5)', opacity: k, transform: `translateX(${(1 - k) * u(c, 2)}px)`,
      }}>
        <div style={{
          width: u(c, 4.2), height: Math.max(1.5, u(c, 0.22)), borderRadius: 2,
          background: `linear-gradient(90deg, ${GOLD}55, ${GOLD} ${lerp(10, 90, sheen)}%, ${GOLD}55)`,
        }} />
        {str(c, 'text', 'www.and-lc.com')}
      </div>
    </AbsoluteFill>
  );
};
export const FOOTER: FxDef = {
  desc: 'A soft dark floor for the subtitles and a small watermark at the bottom right, with a gold rule',
  options: 'text (www.and-lc.com), size (2.5 % of H)',
  Screen: Footer,
};

// ---------- lower third ----------
// A gold bar grows, the glass plate unmasks from it, the name focuses in, the role follows 4 frames later; out the same way.
const Lower: React.FC<{ c: FxCtx }> = ({ c }) => {
  const bar = e('expo.out', c.t, 0, 0.35), plate = e('expo.out', c.t, 0.12, 0.45);
  const n1 = e('expo.out', c.t, 0.22, 0.4), n2 = e('expo.out', c.t, 0.36, 0.4);
  const out = e('power2.in', c.t, c.d - 0.4, 0.4);
  const x = u(c, 5), y = c.H * opt(c, 'y', 0.62), h = u(c, 11.5);
  const vis = 1 - out;
  return (
    <AbsoluteFill>
      <div style={{ position: 'absolute', left: x, top: y, height: h, width: u(c, 0.55), background: GOLD, borderRadius: 2,
        transform: `scaleY(${bar * (1 - out)})`, transformOrigin: '50% 100%' }} />
      <div style={{
        position: 'absolute', left: x + u(c, 0.55), top: y, height: h, boxSizing: 'border-box', padding: `0 ${u(c, 3)}px 0 ${u(c, 2.2)}px`,
        display: 'flex', flexDirection: 'column', justifyContent: 'center', ...glass(c), borderRadius: `0 ${u(c, 1.2)}px ${u(c, 1.2)}px 0`, borderLeft: 'none',
        clipPath: `inset(0 ${(1 - plate * vis) * 100}% 0 0)`, whiteSpace: 'nowrap',
      }}>
        <div style={{ fontFamily: FONT.ui, fontWeight: 700, fontSize: u(c, 3.7), color: '#fff', letterSpacing: '-0.015em', lineHeight: 1.15,
          opacity: n1 * vis, transform: `translateX(${(1 - n1) * -u(c, 3)}px)`, filter: n1 < 0.98 || out > 0 ? `blur(${((1 - n1) + out) * u(c, 0.8)}px)` : undefined }}>
          {str(c, 'name', 'Name')}
        </div>
        <div style={{ fontFamily: FONT.serif, fontStyle: 'italic', fontSize: u(c, 3.4), color: GOLD, lineHeight: 1.15, marginTop: u(c, 0.3),
          opacity: n2 * vis, transform: `translateX(${(1 - n2) * -u(c, 3)}px)`, filter: n2 < 0.98 || out > 0 ? `blur(${((1 - n2) + out) * u(c, 0.8)}px)` : undefined }}>
          {str(c, 'role', 'Role')}
        </div>
      </div>
    </AbsoluteFill>
  );
};
export const LOWER: FxDef = {
  desc: 'Lower third: a gold bar grows, a glass plate unmasks from it with the name and an italic role',
  options: 'name, role, y (0.6 of H)',
  Screen: Lower,
};

// ---------- point card ----------
// A smoked-glass card beside the head (the side with room): an italic serif title, then items that land one by one at
// their own clip times (`at`). Arrives from slightly oversize and focusing, drifts while it holds, sinks and softens out.
const Point: React.FC<{ c: FxCtx }> = ({ c }) => {
  const { face, W, H } = c;
  const side = str(c, 'side', face.x > W / 2 ? 'left' : 'right');
  const w = c.W * opt(c, 'width', 0.3);
  const gap = face.w * 1.05;
  const x = side === 'left' ? clamp(face.x - gap - w, u(c, 4), W) : clamp(face.x + gap, 0, W - u(c, 4) - w);
  const items = list(c, 'items', []);
  const at = list(c, 'at', []).map(Number);
  const t = c.t + c.o.start;
  const k = e('expo.out', c.t, 0, 0.3), out = e('power2.in', c.t, c.d - 0.28, 0.28);
  const drift = Math.sin(c.t * 0.9) * u(c, 0.35);
  const dir = side === 'left' ? 1 : -1;
  const title = str(c, 'title', ''), num = str(c, 'n', '');
  const yc = H * opt(c, 'y', 0.42);
  return (
    <AbsoluteFill>
      <div style={{
        position: 'absolute', left: x, top: yc, width: w, boxSizing: 'border-box', padding: `${u(c, 2.6)}px ${u(c, 2.8)}px`, ...glass(c),
        transform: `translateY(-50%) translateY(${drift + out * u(c, 3)}px) scale(${lerp(1.18, 1, k)}) rotate(${(1 - k) * -4 * dir}deg)`,
        transformOrigin: side === 'left' ? '100% 50%' : '0% 50%',
        opacity: clamp(k * 3) * (1 - out), filter: k < 0.98 || out > 0.01 ? `blur(${((1 - k) + out) * u(c, 1)}px)` : undefined,
      }}>
        {num ? <div style={{ fontFamily: FONT.ui, fontWeight: 800, fontSize: u(c, 3.2), letterSpacing: '0.08em', lineHeight: 1, color: GOLD, marginBottom: u(c, 1.1) }}>{num}</div> : null}
        {title ? <div style={{ fontFamily: FONT.serif, fontStyle: 'italic', fontSize: u(c, opt(c, 'tsize', 6.2)), lineHeight: 1.08, color: '#fff' }}>{title}</div> : null}
        {items.length ? <div style={{ height: Math.max(1, u(c, 0.15)), background: `linear-gradient(90deg, ${GOLD}, ${GOLD}00)`, margin: `${u(c, 1.6)}px 0 ${u(c, 1.2)}px`,
          transform: `scaleX(${e('expo.out', c.t, 0.15, 0.5)})`, transformOrigin: '0 50%' }} /> : null}
        {items.map((it, i) => {
          const ik = e('expo.out', t, (at[i] ?? c.o.start + 0.25 + i * 0.25) - 2 / 30, 0.3);
          return (
            <div key={i} style={{
              display: 'flex', gap: u(c, 1.2), alignItems: 'baseline', fontFamily: FONT.ui, fontWeight: 600, fontSize: u(c, opt(c, 'isize', 3.6)),
              lineHeight: 1.25, color: 'rgba(255,255,255,0.94)', marginTop: i ? u(c, 1) : 0,
              opacity: clamp(ik * 2.5), transform: `translateX(${(1 - ik) * u(c, 2.5) * -dir}px)`, filter: ik < 0.98 ? `blur(${(1 - ik) * u(c, 0.7)}px)` : undefined,
            }}>
              <span style={{ width: u(c, 0.9), height: u(c, 0.9), borderRadius: '50%', background: GOLD, flex: 'none', transform: `translateY(-${u(c, 0.45)}px)` }} />
              <span>{it}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
export const POINT: FxDef = {
  desc: 'A smoked-glass point card beside the head: italic serif title, items landing one by one at their own times',
  options: 'title, n (big gold numeral), items (a | b), at (clip seconds per item), side (left | right), y (0.42), width (0.29), tsize, isize',
  Front: Point,
  frontDepth: 'screen',
};

// ---------- quote: a large serif line behind the head ----------
// The quieter cousin of text-behind for whole phrases: a centred italic serif line high in the frame, behind the head,
// focusing up word by word and lifting slowly.
const Quote: React.FC<{ c: FxCtx }> = ({ c }) => {
  const words = str(c, 'text', '').split(/\s+/).filter(Boolean);
  const out = e('power2.in', c.t, c.d - 0.35, 0.35);
  const fs = u(c, opt(c, 'size', 9));
  const lift = c.t * u(c, 0.35);
  return (
    <AbsoluteFill>
      <div style={{
        position: 'absolute', left: c.W * 0.06, width: c.W * 0.88, top: c.H * opt(c, 'y', 0.13) - lift - out * u(c, 2), textAlign: 'center',
        fontFamily: FONT.serif, fontStyle: 'italic', fontSize: fs, lineHeight: 1.02, color: str(c, 'color', '#ffffff'),
        textShadow: `0 ${u(c, 1)}px ${u(c, 4)}px rgba(0,0,0,0.35)`, opacity: 1 - out, filter: out > 0.01 ? `blur(${out * u(c, 1.4)}px)` : undefined,
      }}>
        {words.map((w0, i) => {
          const gold = /^\*.*\*[.,?!:;]*$/.test(w0), w = w0.replace(/\*/g, '');
          const k = e('expo.out', c.t, i * 0.09, 0.45);
          return <span key={i} style={{ display: 'inline-block', whiteSpace: 'pre', color: gold ? GOLD : undefined, opacity: clamp(k * 2),
            transform: `translateY(${(1 - k) * fs * 0.4}px)`, filter: k < 0.98 ? `blur(${(1 - k) * fs * 0.12}px)` : undefined }}>{w}{i < words.length - 1 ? ' ' : ''}</span>;
        })}
      </div>
    </AbsoluteFill>
  );
};
export const QUOTE: FxDef = {
  desc: 'A large italic serif phrase behind the head, words focusing up one by one, lifting slowly',
  options: 'text (*gold* words), size (9 % of H), y (0.13), color',
  Behind: Quote,
  depth: 'screen',
};

// ---------- B-roll cutaway ----------
// A full-frame clip opens from the centre like curtains (a thin gold seam at each edge), focusing down from 1.12 while it
// plays a slow push; it leaves by wiping off to the right behind a single gold seam, uncovering the speaker. `src` is a
// file in the job folder, `rate` the playback speed (fits the clip to the window), `from` seconds into the clip.
const Broll: React.FC<{ c: FxCtx }> = ({ c }) => {
  const k = e('expo.out', c.t, 0, 0.55);
  const out = e('power3.in', c.t, c.d - 0.5, 0.5);
  const push = lerp(1.12, 1.05, k) - 0.05 * clamp(c.t / c.d);
  const open = (1 - k) * 50;                       // inset from both sides while it opens
  const wipe = out * 100;                          // inset from the left while it leaves
  const seam = Math.max(2, u(c, 0.35));
  const from = Math.round(c.o.start * c.fps);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ clipPath: `inset(0 ${open}% 0 ${Math.max(open, wipe)}%)`, overflow: 'hidden', background: '#0b0c0f' }}>
        <AbsoluteFill style={{ transform: `scale(${push - out * 0.03})`, filter: `contrast(1.05) saturate(0.94)${k < 0.97 ? ` blur(${(1 - k) * u(c, 0.9)}px)` : ''}` }}>
          <Sequence from={from} layout="none">
            <OffthreadVideo muted src={staticFile(str(c, 'src', 'broll/a.mp4'))} playbackRate={opt(c, 'rate', 1)}
              trimBefore={Math.round(opt(c, 'from', 0) * c.fps)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </Sequence>
        </AbsoluteFill>
        <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.38) 100%)' }} />
      </AbsoluteFill>
      {k < 0.995 ? <>
        <div style={{ position: 'absolute', top: 0, bottom: 0, width: seam, left: `calc(${open}% - ${seam / 2}px)`, background: GOLD, opacity: 1 - k }} />
        <div style={{ position: 'absolute', top: 0, bottom: 0, width: seam, right: `calc(${open}% - ${seam / 2}px)`, background: GOLD, opacity: 1 - k }} />
      </> : null}
      {out > 0.001 && out < 0.999 ? (
        <div style={{ position: 'absolute', top: 0, bottom: 0, width: seam, left: `calc(${wipe}% - ${seam / 2}px)`, background: GOLD,
          boxShadow: `0 0 ${u(c, 2)}px ${GOLD}aa` }} />
      ) : null}
    </AbsoluteFill>
  );
};
export const BROLL: FxDef = {
  desc: 'B-roll cutaway: a full-frame clip opens from the centre with gold seams, slow push, wipes off to the right',
  options: 'src (file in the job folder), rate (playback speed), from (seconds into the clip)',
  Screen: Broll,
};
