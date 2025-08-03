import { SpeechRecognizer } from './speech.js';
import { WSClient } from '../ws/wsclient.js';
import config from './config.js';


//  SECTION:============================================================= 
//            Functions, setup     
//  ===================================================================== 

function setupDom() {

  if (!config) {
    console.error("No config");
    return;
  }

  // build selectbox for recognition languages.
  config.languages.forEach(lang => {
    const opt = document.createElement('option');
    opt.value = lang.code;
    opt.textContent = lang.label;
    langSelect.appendChild(opt);
  });
  langSelect.value = recogLangCode;

  // ====== UI handlers
  startBtn.onclick = startListen;
  stopBtn.onclick = stopListen;
  langSelect.onchange = selectRecogLang;

}

//  SECTION:============================================================= 
//            Functions, web page UI     
//  ===================================================================== 

function startListen() {
  if (!recognizer) throw new Error("recognizer required.");
  recognizer.start();
  recognizing = true;
  startBtn.disabled = true;
  stopBtn.disabled = false;
}

function stopListen() {
  if (recognizer && recognizing) {
    recognizer.stop();
    recognizing = false;
  }
  startBtn.disabled = false;
  stopBtn.disabled = true;
}

function selectRecogLang() {
  if (recognizer) {
    recognizer.setLanguage(langSelect.value);
    recognizer.stop();
  }
  setRecogLangCode(langSelect.value);
  // recogLangCode = langSelect.value;
  // restart recognition. stopListen() includes start recognition.
  updateCurrentLangDisplay();
}

function displayRecogText(recogText, isFinal, recogLangCode) {
  resultDiv.textContent = `[${recogLangCode}]${isFinal ? '[Final] ' : '[Interim] '}\n${recogText}`;
}

function updateCurrentLangDisplay() {
  // currentLangSpan.textContent = `Current: ${selected?.label || ''}`;
  currentLangSpan.textContent = `Current: ${recogLangLabel}`;
}

function getRecogLangLabel(langCode = recogLangCode, languages = config.languages) {
  if (!languages) return;
  const lang = languages.find(l => l.code === langCode);
  return lang ? lang.label : null;
}

// Set recognition language code. and set its label.
function setRecogLangCode(newRecogLangCode) {
  recogLangCode = newRecogLangCode;
  recogLangLabel = getRecogLangLabel(recogLangCode);
}

//  SECTION:============================================================= 
//            Functions, speech recognition     
//  ===================================================================== 

// ====== Setup functions of speech recogntion object.
// Handlers for setupRecognizer():
function onResult(recogText, isFinal) {
  // send recognition result
  sendRecognitionResult(wsclient, recogText, isFinal);
  displayRecogText(recogText, isFinal, recogLangCode);
}

function onError(error) {
  alert('Speech recognition error: ' + error);
}
function onEnd() {
  if (recognizing) recognizer.start(); // auto-restart for continuous recognition
}

// Instantiate recognizer with initial language
function setupRecognizer(lang, noSpeechMs = config.noSpeechMs) {
  recognizer = new SpeechRecognizer({
    lang: lang,
    noSpeechMs: noSpeechMs,
    onResult,
    onError,
    onEnd
  });
}

//  SECTION:============================================================= 
//            Functions, websocket
//  ===================================================================== 

let lastSendTime = 0;
let lastSendText = '';
// Sends text with websocket. Interval of sending is over throttle time.
// Returns true when text is send, false when not.
function sendRecognitionResult(ws, recogText, isFinal, throttleTime = config.throttleTime) {
  console.log("send text");
  const data = {
    recogText: recogText,
    isFinal: isFinal,
    language: {
      code: recogLangCode,
      label: recogLangLabel,
    }
  };

  const now = Date.now();

  if (isFinal) {
    ws.send(JSON.stringify(data));
    return true;
  } else {
    if (data.recogText !== lastSendText) {
      if (now - lastSendTime > throttleTime) {
        console.log("before send");
        ws.send(JSON.stringify(data));
        lastSendText = recogText;
        lastSendTime = now;
        return true;
      }
    }
  }
  // console.log("no send");
  return false;
}

//  SECTION:============================================================= 
//            Variables     
//  ===================================================================== 


// Read config values
if (!config) {
  console.error("No config.");
}

let wsclient = new WSClient({ url: config.urlSpeechRecognitionWs });
let recogLangCode = config.deafultLanguageCode;
let recogLangLabel = getRecogLangLabel(recogLangCode);

// DOM elements
const currentLangSpan = document.getElementById('currentLang');
const resultDiv = document.getElementById('result');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const langSelect = document.getElementById('language');

let recognizer = null;
let recognizing = false;




//  SECTION:============================================================= 
//            Main loop
//  ===================================================================== 

console.log("start");

setupDom();
// Instantiate recognizer to use WebKitSpeechRecognition
setupRecognizer(recogLangCode);


window.addEventListener('DOMContentLoaded', () => {
  // Automatically start speech recognition when page loads
  startListen();
  // update text of recognition lanuage in web page.
  updateCurrentLangDisplay();
});
