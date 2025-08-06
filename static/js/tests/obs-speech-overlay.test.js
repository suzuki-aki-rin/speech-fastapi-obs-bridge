// Tests for ../static/js/obs-speech-overlay/obs-speech-overlay.js
// Use them by import in obs-speech-overlay.js
// Maybe, Test by using showMessage imported seems good. But I do not know 
// what to do.
import { showMessage } from "../obs-speech-overlay/obs-speech-overlay.js";

// Tests showMessage() when receiving original text
export function testShowMesasgeOriginals() {
  const argsIntervals = [
    { arg: JSON.stringify({ type: 'original', recogText: "Hello someone very very very very very long sentences. ohhhhhhhhhhhhhhhhhhhhhhh.", isFinal: false }), interval: 1 },
    { arg: JSON.stringify({ type: 'original', recogText: "Hello someone2", isFinal: false }), interval: 2 },
    { arg: JSON.stringify({ type: 'original', recogText: "Hello someone3", isFinal: true }), interval: 2 },
    { arg: JSON.stringify({ type: 'original', recogText: "Hello someone4", isFinal: true }), interval: 3 },
  ];

  repeatFuncInterval(showMessage, argsIntervals);
}

// Tests showMessage() when receiving translated text
export function testShowMesasgeTranslated(params) {
  const argsIntervals = [
    { arg: JSON.stringify({ type: 'translated', transText: "Hello someone very very very very very long sentences. ohhhhhhhhhhhhhhhhhhhhhhh.", origLang: 'jp-ja', transLang: 'en-en' }), interval: 1 },
    { arg: JSON.stringify({ type: 'translated', transText: "Hello2", origLang: 'jp-ja', transLang: 'en-en' }), interval: 1 },
    { arg: JSON.stringify({ type: 'translated', transText: "Hello3", origLang: 'jp-ja', transLang: 'en-en' }), interval: 1 },
    { arg: JSON.stringify({ type: 'translated', transText: "Hello4", origLang: 'jp-ja', transLang: 'en-en' }), interval: 1 },
  ];
  repeatFuncInterval(showMessage, argsIntervals);
}


// 1秒待つための関数（Promise）
function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// argsIntervalsは [{ arg: any, interval: number }, ...] の形
async function repeatFuncInterval(func, argsIntervals) {
  for (const { arg, interval } of argsIntervals) {
    func(arg);
    await wait(interval * 1000); // 秒→ミリ秒
  }
}

