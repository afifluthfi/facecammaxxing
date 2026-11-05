import { continueRender, delayRender, staticFile } from 'remotion';

// Fonts are served from the job folder (fonts/*.woff2), so rendering needs no access to Google Fonts.
type Face = [family: string, file: string, weight: string, style: string];
const FACES: Face[] = [
  ['FCM Anton', 'anton-400-normal.woff2', '400', 'normal'],
  ['FCM Archivo Black', 'bold-400-normal.woff2', '400', 'normal'],
  ['FCM Inter', 'ui-500-normal.woff2', '500 800', 'normal'],
  ['FCM Instrument Serif', 'serif-400-italic.woff2', '400', 'italic'],
  ['FCM Space Mono', 'mono-400-normal.woff2', '400', 'normal'],
  ['FCM Space Mono', 'mono-700-normal.woff2', '700', 'normal'],
  ['FCM Parisienne', 'script-400-normal.woff2', '400', 'normal'],
];

const handle = delayRender('fonts');
export const fontsReady = Promise.all(FACES.map(async ([family, file, weight, style]) => {
  const f = new FontFace(family, `url(${staticFile(`fonts/${file}`)}) format('woff2')`, { weight, style });
  await f.load();
  (document.fonts as unknown as { add: (f: FontFace) => void }).add(f);
}));
fontsReady.then(() => continueRender(handle));

export const FONT = {
  anton: 'FCM Anton', bold: 'FCM Archivo Black', ui: 'FCM Inter', serif: 'FCM Instrument Serif', mono: 'FCM Space Mono', script: 'FCM Parisienne',
} as const;
export type FontKey = keyof typeof FONT;
