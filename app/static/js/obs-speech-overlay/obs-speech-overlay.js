import { WSClient } from '../ws/wsclient.js';
import { TextSlider, RecogTextDisplay } from './line-slide-container.js';
import config from './config.js';
import { testShowMesasgeOriginals } from '../tests/obs-speech-overlay.test.js';

//  SECTION:=============================================================
//            Constants
//  =====================================================================


//  SECTION:============================================================= 
//            Functions, websocket client     
//  ===================================================================== 

function onClose() {
  console.info("the connection was closed.");
}

function onError(e) {
  console.error("the connection got error.", { e });
}

function onMessage(message) {
  // console.log("message received");
  if (message === config.heartbeat) {
    // Reset connection timeout or ignore heartbeat message
    console.debug("Received heartbeat");
    speechOverlay.wsClinent.send("pong");
    console.debug("send pong");
    return;
  }
  speechOverlay.showMessage(message);
}


//  SECTION:=============================================================
//            Class: SpeechOverlay
//  =====================================================================

class SpeechOverlay {
  constructor() {
    this.wsClinent = null;
    this.RecogTextDisplay = new RecogTextDisplay("#recog-display", { isUpward: true, isAlignRight: true, });
    this.transTextDisplay = new TextSlider("#trans-display", { isUpward: true, isAlignRight: true, });
  }
  showMessage(message) {
    const obj = JSON.parse(message);
    // console.log("type: '" + obj.type + "'");
    switch (obj.type) {
      case 'original':
        this.RecogTextDisplay.displayMessage(obj);
        break;
      case 'translated':
        this.transTextDisplay.pushText(obj.translated_text);
        break;
      default:
        console.error("Received bad json.");
        break;
    }
  }

  start() {
    this.wsClinent = new WSClient({
      url: config.urlObsSpeechOverlayWs, onMessage, onClose, onError
    });
  }
}
//  SECTION:=============================================================
//            Functions, Display
//  =====================================================================

// received data structure
// original text:
// {
//   recogText: recogText,
//   isFinal: isFinal,
//   language: {
//     code: recogLangCode,
//     label: recogLangLabel,
//   },
//   type: "original",
// }
//
// translated text:
// {
// "translated_text": translated_text,
// "original_text": original_text,
// "source_language": self.source_lang,
// "target_language": self.target_lang,
// Shows text in broser.
// This function recieves two type of messages: recognition, translated.



function showMessageDemo() {
  /* --- Simulation for demo --- */
  const dataStream = [
    { type: "original", isFinal: false, recogText: 'Hello' },
    { type: "original", isFinal: false, recogText: 'Hello wor' },
    { type: "original", isFinal: true, recogText: 'Hello world.' },
    { type: "original", isFinal: false, recogText: 'How' },
    { type: "original", isFinal: false, recogText: 'How are' },
    { type: "original", isFinal: true, recogText: 'How are you?' },
    { type: "original", isFinal: false, recogText: 'How' },
    { type: "original", isFinal: true, recogText: 'This is a test.' },
    { type: "original", isFinal: false, recogText: 'こんにちは あつ.' },
    { type: "original", isFinal: true, recogText: 'こんにちは、暑いですね' },
    { type: "original", isFinal: false, recogText: 'How' },
    { type: "original", isFinal: true, recogText: 'Streaming is fun.' },
    { type: "original", isFinal: false, recogText: 'How' },
    { type: "original", isFinal: true, recogText: 'We keep only five lines.' },
    { type: "original", isFinal: false, recogText: 'How' },
    { type: "original", isFinal: true, recogText: 'Older lines disappear.' },
    { type: "original", isFinal: false, recogText: 'How' },
    { type: "original", isFinal: true, recogText: 'This is the newest one.' }
  ];
  const dataStreamTrans = [
    { type: "translated", isFinal: false, translated_text: 'Hello' },
    { type: "translated", isFinal: false, translated_text: 'Hello wor' },
    { type: "translated", isFinal: true, translated_text: 'Hello world.' },
    { type: "translated", isFinal: false, translated_text: 'How' },
    { type: "translated", isFinal: false, translated_text: 'How are' },
    { type: "translated", isFinal: true, translated_text: 'How are you?' },
    { type: "translated", isFinal: false, translated_text: 'How' },
    { type: "translated", isFinal: true, translated_text: 'This is a test.' },
    { type: "translated", isFinal: false, translated_text: 'こんにちは あつ.' },
    { type: "translated", isFinal: true, translated_text: 'こんにちは、暑いですね' },
    { type: "translated", isFinal: false, translated_text: 'How' },
    { type: "translated", isFinal: true, translated_text: 'Streaming is fun.' },
    { type: "translated", isFinal: false, translated_text: 'How' },
    { type: "translated", isFinal: true, translated_text: 'We keep only five lines.' },
    { type: "translated", isFinal: false, translated_text: 'How' },
    { type: "translated", isFinal: true, translated_text: 'Older lines disappear.' },
    { type: "translated", isFinal: false, translated_text: 'How' },
    { type: "translated", isFinal: true, translated_text: 'This is the newest one.' }
  ];
  // const dataStream = [
  //   { id: 1, type: 'interim', text: 'Hello' },
  //   { id: 1, type: 'interim', text: 'Hello wor' },
  //   { id: 1, type: 'final', text: 'Hello world.' },
  //   { id: 2, type: 'interim', text: 'How' },
  //   { id: 2, type: 'interim', text: 'How are' },
  //   { id: 2, type: 'final', text: 'How are you?' },
  //   { id: 2, type: 'interim', text: 'How' },
  //   { id: 1, type: 'final', text: 'This is a test.' },
  //   { id: 2, type: 'interim', text: 'How' },
  //   { id: 2, type: 'final', text: 'Streaming is fun.' },
  //   { id: 2, type: 'interim', text: 'How' },
  //   { id: 1, type: 'final', text: 'We keep only five lines.' },
  //   { id: 2, type: 'interim', text: 'How' },
  //   { id: 2, type: 'final', text: 'Older lines disappear.' },
  //   { id: 2, type: 'interim', text: 'How' },
  //   { id: 2, type: 'final', text: 'This is the newest one.' }
  // ];


  const speechOverlay = new SpeechOverlay();

  let i = 0;
  let timer = setInterval(() => {
    if (i >= dataStream.length) {
      clearInterval(timer);
      return;
    }
    speechOverlay.showMessage(JSON.stringify(dataStream[i]));
    speechOverlay.showMessage(JSON.stringify(dataStreamTrans[i]));
    i++;
  }, 800);
}
//  SECTION:============================================================= 
//            Main loop     
//  ===================================================================== 

const speechOverlay = new SpeechOverlay();
speechOverlay.start();
//
// showMessageDemo();
