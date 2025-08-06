import { WSClient } from '../ws/wsclient.js';
import config from './config.js';

import { testShowMesasgeOriginals, testShowMesasgeTranslated } from '../tests/obs-speech-overlay.test.js';
// import {
//     LANGUAGES,
//     DEFAULT_LANGUAGE_CODE,
//     NO_SPEECH_TIMEOUT,
//     URL_WS_SPEECH_RECOGNITION
// } from './config.js';

//  SECTION:============================================================= 
//            Constants     
//  ===================================================================== 

const idNewOrig = 'newOriginal';
const idNewTranslated = 'newTranslated';
const idOldOrig = 'oldOriginal';
const idOldTranslated = 'oldTranslated';
const idTranslatedContainer = 'translatedSubtitle';


//  SECTION:============================================================= 
//            Functions     
//  ===================================================================== 

// Append textNode and some elements to newOriginal, that is for display of recognition text.
// Returns {textNode: textNode, dots: dots}
// Added to use dots animation.
function appendTextNodeEtcToNewOriginal() {
  // Build a element for new recognition text
  const textNode = document.createTextNode('');
  const dots = document.createElement('span');
  dots.className = 'typing';
  dots.classList.add('hidden');
  // add dot x3. The dot is described in .css.
  for (let i = 0; i < 3; i++) {
    const dotSpan = document.createElement('span');
    dotSpan.className = 'dot';
    dots.appendChild(dotSpan);
  }
  newOriginal.appendChild(dots);
  newOriginal.appendChild(textNode);

  return { textNode: textNode, dots: dots };
}



function onMessage(message) {
  console.log("onmessage");
  showMessage(message);
}

// received data structure
// const data = {
//   recogText: recogText,
//   isFinal: isFinal,
//   language: {
//     code: recogLangCode,
//     label: recogLangLabel,
//   }
//   
// 

// Shows text in broser.
// This function recieves two type of messages: recognition, translated.
export function showMessage(message) {
  const obj = JSON.parse(message);
  console.log("type: ", obj.type);

  switch (obj.type) {
    case 'original':
      const recogText = obj.recogText;
      const isFinal = obj.isFinal;
      // recognition text is not final, add ... prompt
      if (isFinal) { dots.classList.add('hidden'); }
      else { dots.classList.remove('hidden'); }

      updateNewOriginal(recogText, isFinal, config.eraseTimeMsec);
      break;
    case 'translated':
      // TODO:
      const text = obj.transText;
      updateNewTranslated(text, config.eraseTimeMsec);
      break;
    default:
      console.error("Received bad json.");
      break;
  }
}



// Updates text of nodes that has tranlated text area to show.
function updateNewTranslated(text, eraseTime) {
  updateTextEraseLater(newTranslated, text, eraseTime, oldTranslated);
}

let updateTimeout = null;
let lastFinalText = "";
// Updates text of element that shows recognition text. The text is final recognition or not.
// When final, update text and copy it to text history area, #oldOriginal.
// eraseTime has passed after update, text shown is erased.
function updateNewOriginal(recogText, isFinal, eraseTime) {
  updateText(textNode, recogText);
  if (isFinal) {
    if (updateTimeout) { clearTimeout(updateTimeout); }
    if (lastFinalText) {
      updateText(oldOriginal, lastFinalText);
    }
    lastFinalText = recogText;
    updateTimeout = setTimeout(() => {
      // updateText(oldOriginal, textNode.textContent);
      updateTextEraseLater(oldOriginal, textNode.textContent, eraseTime);
      eraseText(textNode);
      updateTimeout = null;
    }, eraseTime);
  }
}

const timeouts = new WeakMap();
// Updates node text and erase it later. When copying text to element before erasing,
// set the element to copyTo.
function updateTextEraseLater(node, newText, eraseTime, copyTo = null) {
  const oldText = getNodeText(node);
  updateText(node, newText);

  const existingTimeout = timeouts.get(node);
  if (existingTimeout) {
    clearTimeout(existingTimeout);
    if (copyTo) updateTextEraseLater(copyTo, oldText, eraseTime);
  }
  const newTimeout = setTimeout(() => {
    if (copyTo) {
      updateTextEraseLater(copyTo, getNodeText(node), eraseTime);
    }
    eraseText(node);
    timeouts.delete(node);
  }, eraseTime);

  timeouts.set(node, newTimeout);
}

// Updates text of node. And add class .has-text to show backgroud-color.
function updateText(node, newText) {
  node.textContent = newText;

  if (isTextNode(node)) node = node.parentElement;
  node.classList.add('has-text');
}

// Erases text of node. And remove class .has-text to hide backgroud-color.
function eraseText(node) {
  node.textContent = '';

  if (isTextNode(node)) node = node.parentElement;
  node.classList.remove('has-text');
}

function getNodeText(node) {
  return node.textContent;

}

function isTextNode(node) {
  return node && node.nodeType === Node.TEXT_NODE;
}

function hideElem(elem) {
  elem.classList.add('hidden');
}


//  SECTION:============================================================= 
//            Main loop     
//  ===================================================================== 

// Get DOM elements to access
const newOriginal = document.getElementById(idNewOrig);
const newTranslated = document.getElementById(idNewTranslated);
const oldOriginal = document.getElementById(idOldOrig);
const oldTranslated = document.getElementById(idOldTranslated);
const translatedContainer = document.getElementById(idTranslatedContainer);


if (!config.showTranslated) {
  hideElem(translatedContainer);
}

const wsclient = new WSClient({ url: config.urlObsSpeechOverlayWs, onMessage });

const { textNode: textNode, dots: dots } = appendTextNodeEtcToNewOriginal();



// testShowMesasgeOriginals();
// testShowMesasgeTranslated();
