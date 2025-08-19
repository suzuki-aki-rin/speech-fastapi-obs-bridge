import { WSClient } from '../ws/wsclient.js';
import config from './config.js';
import { testShowMesasgeOriginals } from '../tests/obs-speech-overlay.test.js';

//  SECTION:=============================================================
//            Constants
//  =====================================================================

const MAX_HISTORY_LENGTH = 1;

//  SECTION:============================================================= 
//            Functions     
//  ===================================================================== 

// Append textNode and some elements to newOriginal, that is for display of recognition text.
// Returns {textNode: textNode, dots: dots}
// Added to use dots animation.
// function appendTextNodeEtcToNewOriginal() {
//   // Build a element for new recognition text
//   const textNode = document.createTextNode('');
//   const dots = document.createElement('span');
//   dots.className = 'typing';
//   dots.classList.add('hidden');
//   // add dot x3. The dot is described in .css.
//   for (let i = 0; i < 3; i++) {
//     const dotSpan = document.createElement('span');
//     dotSpan.className = 'dot';
//     dots.appendChild(dotSpan);
//   }
//   newOriginal.appendChild(textNode);
//   newOriginal.appendChild(dots);
//
//   return { textNode: textNode, dots: dots };
// }

//  SECTION:============================================================= 
//            Functions, websocket client     
//  ===================================================================== 


function onClose() {
  console.debug("the connection was closed.")
}

function onError(e) {
  console.debug("the connection got error.", { e })
}

function onMessage(message) {
  // console.log("message received");
  if (message === config.heartbeat) {
    // Reset connection timeout or ignore heartbeat message
    console.debug("Received heartbeat");
    wsclient.send("pong");
    console.debug("send pong");
    return;
  }

  showMessage(message);
}

//  SECTION:=============================================================
//            Functions, Display
//  =====================================================================
function showElemFadeOther(text, shownElem, fadedElem, shownElemOriginalOpacity, fadedElemOriginalOpacity, fadeTimeMsec) {
  fadedElem.style.opacity = 0;
  shownElem.style.opacity = shownElemOriginalOpacity;
  setTimeout(() => {
    shownElem.textContent = text;
    fadedElem.textContent = '';
    fadedElem.style.opacity = fadedElemOriginalOpacity;
  }, fadeTimeMsec);
}



// <div dataset-id
function createHistoryElements(divHistories, arrayHistoryElems, historyMaxNumber) {
  for (let i = 0; i < historyMaxNumber; i++) {
    const elem = document.createElement('div');
    // elem.dataset.id = MAX_HISTORY_LENGTH - i;
    elem.dataset.id = i;
    elem.className = "history";
    // elem.textContent = (MAX_HISTORY_LENGTH - i ).toString();
    elem.textContent = i.toString();
    arrayHistoryElems.push(elem);
    divHistories.appendChild(elem);
  }
}


function updateHistory(arrayHistories, arrayHistoryElems, historyContainer, slideDurationMsec) {
  // When textHistory.length < textHistoryElems, set text to textHistoryElems[diff + i]
  const diff = arrayHistoryElems.length - arrayHistories.length;
  arrayHistories.forEach((text, i) => {
    const elem = arrayHistoryElems[diff + i];
    elem.textContent = text;
  });
  slideHistoryContaier(historyContainer, slideDurationMsec);

}

// let cnt = 0;
function slideHistoryContaier(historyContainer, slideDurationMsec) {
  // console.log("counter: ", cnt);
  // cnt++;
  requestAnimationFrame(() => {
    historyContainer.classList.add("show");
    setTimeout(() => {
      historyContainer.classList.remove("show");
    }, slideDurationMsec);
  });
}


function sendToHistory(text, arrayHistories, maxHistoryLength,) {
  if (arrayHistories.length >= maxHistoryLength) {
    arrayHistories.shift();
  }
  arrayHistories.push(text);
}



function updateRecogText(isFinal, text, historyContainer, maxHistoryLength
  , fadeTimeMsec, arrayHistories, arrayHistoryElems, slideDurationMsec) {
  if (!isFinal) {
    if (finalSpan.textContent) {
      showElemFadeOther(text, interimSpan, finalSpan, interimSpanOrigOpacity, finalSpanOrigOpacity, fadeTimeMsec);
      updateHistory(arrayHistories, arrayHistoryElems, historyContainer, slideDurationMsec);
    }
    else {
      interimSpan.style.opacity = interimSpanOrigOpacity;
      interimSpan.textContent = text;
    }
  } else {
    showElemFadeOther(text, finalSpan, interimSpan, finalSpanOrigOpacity, interimSpanOrigOpacity, fadeTimeMsec);
    sendToHistory(text, arrayHistoryRecogTexts, maxHistoryLength);
  }
}
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
// "type": self.result_type,
// }
// Shows text in broser.
// This function recieves two type of messages: recognition, translated.
export function showMessage(message) {
  const obj = JSON.parse(message);
  // console.log("type: '" + obj.type + "'");
  switch (obj.type) {
    case 'original':
      const recogText = obj.recogText;
      const isFinal = obj.isFinal;
      // // recognition text is not final, add ... prompt
      // if (isFinal) { dots.classList.add('hidden'); }
      // else { dots.classList.remove('hidden'); }
      updateRecogText(isFinal, recogText, divHistoryRecogText, MAX_HISTORY_LENGTH, 200, arrayHistoryRecogTexts, arrayHistoryRecogTextElems, 400)

      // updateNewOriginal(recogText, isFinal, config.eraseTimeMsec);
      break;
    case 'translated':
      // const text = obj.translated_text;
      // console.log("translated: ", text);
      // updateNewTranslated(text, config.eraseTimeMsec);
      break;
    default:
      console.error("Received bad json.");
      break;
  }
}


// Shows text in broser.
// This function recieves two type of messages: recognition, translated.
// export function showMessage(message) {
//   const obj = JSON.parse(message);
//   // console.log("type: '" + obj.type + "'");
//   switch (obj.type) {
//     case 'original':
//       const recogText = obj.recogText;
//       const isFinal = obj.isFinal;
//       // recognition text is not final, add ... prompt
//       if (isFinal) { dots.classList.add('hidden'); }
//       else { dots.classList.remove('hidden'); }
//
//       updateNewOriginal(recogText, isFinal, config.eraseTimeMsec);
//       break;
//     case 'translated':
//       const text = obj.translated_text;
//       console.log("translated: ", text);
//       updateNewTranslated(text, config.eraseTimeMsec);
//       break;
//     default:
//       console.error("Received bad json.");
//       break;
//   }
// }
//
//
//
// // Updates text of nodes that has tranlated text area to show.
// function updateNewTranslated(text, eraseTime) {
//   updateTextEraseLater(newTranslated, text, eraseTime, oldTranslated);
// }
//
// let updateTimeout = null;
// let lastFinalText = "";
// // Updates text of element that shows recognition text. The text is final recognition or not.
// // When final, update text and copy it to text history area, #oldOriginal.
// // eraseTime has passed after update, text shown is erased.
// function updateNewOriginal(recogText, isFinal, eraseTime) {
//   updateText(newOriginaltextNode, recogText);
//   if (isFinal) {
//     if (updateTimeout) { clearTimeout(updateTimeout); }
//     // Update text of #oldOriginal when final text is updated.
//     // If there is no text in #oldOriginal, do not update.
//     if (lastFinalText && oldOriginal.textContent) {
//       updateTextEraseLater(oldOriginal, lastFinalText, eraseTime);
//     }
//     lastFinalText = recogText;
//     updateTimeout = setTimeout(() => {
//       // updateText(oldOriginal, textNode.textContent);
//       updateTextEraseLater(oldOriginal, newOriginaltextNode.textContent, eraseTime);
//       eraseText(newOriginaltextNode);
//       updateTimeout = null;
//     }, eraseTime);
//   }
// }
//
// const timeouts = new WeakMap();
// // Updates node text and erase it later. When copying text to element before erasing,
// // set the element to copyTo.
// function updateTextEraseLater(node, newText, eraseTime, copyTo = null) {
//   const oldText = getNodeText(node);
//   updateText(node, newText);
//
//   const existingTimeout = timeouts.get(node);
//   if (existingTimeout) {
//     clearTimeout(existingTimeout);
//     if (copyTo) updateTextEraseLater(copyTo, oldText, eraseTime);
//   }
//   const newTimeout = setTimeout(() => {
//     if (copyTo) {
//       updateTextEraseLater(copyTo, getNodeText(node), eraseTime);
//     }
//     eraseText(node);
//     timeouts.delete(node);
//   }, eraseTime);
//
//   timeouts.set(node, newTimeout);
// }
//
// // Updates text of node. And add class .has-text to show backgroud-color.
// function updateText(node, newText) {
//   node.textContent = newText;
//
//   if (isTextNode(node)) node = node.parentElement;
//   node.classList.add('has-text');
// }
//
// // Erases text of node. And remove class .has-text to hide backgroud-color.
// function eraseText(node) {
//   node.textContent = '';
//
//   if (isTextNode(node)) node = node.parentElement;
//   node.classList.remove('has-text');
// }
//
// function getNodeText(node) {
//   return node.textContent;
//
// }
//
// function isTextNode(node) {
//   return node && node.nodeType === Node.TEXT_NODE;
// }
//
// function hideElem(elem) {
//   elem.classList.add('hidden');
// }
//
//
function getElemOpacity(elem) {
  const style = window.getComputedStyle(elem);
  return style.getPropertyValue("opacity");
}

function showMessageDemo() {
  /* --- Simulation for demo --- */
  const dataStream = [
    { type: "original", isFinal: false, text: 'Hello' },
    { type: "original", isFinal: false, text: 'Hello wor' },
    { type: "original", isFinal: true, text: 'Hello world.' },
    { type: "original", isFinal: false, text: 'How' },
    { type: "original", isFinal: false, text: 'How are' },
    { type: "original", isFinal: true, text: 'How are you?' },
    { type: "original", isFinal: false, text: 'How' },
    { type: "original", isFinal: true, text: 'This is a test.' },
    { type: "original", isFinal: false, text: 'こんにちは あつ.' },
    { type: "original", isFinal: true, text: 'こんにちは、暑いですね' },
    { type: "original", isFinal: false, text: 'How' },
    { type: "original", isFinal: true, text: 'Streaming is fun.' },
    { type: "original", isFinal: false, text: 'How' },
    { type: "original", isFinal: true, text: 'We keep only five lines.' },
    { type: "original", isFinal: false, text: 'How' },
    { type: "original", isFinal: true, text: 'Older lines disappear.' },
    { type: "original", isFinal: false, text: 'How' },
    { type: "original", isFinal: true, text: 'This is the newest one.' }
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



  let i = 0;
  let timer = setInterval(() => {
    if (i >= dataStream.length) {
      clearInterval(timer);
      return;
    }
    const { type, isFinal, text } = dataStream[i];
    updateRecogText(isFinal, text, divHistoryRecogText, MAX_HISTORY_LENGTH, 200, arrayHistoryRecogTexts, arrayHistoryRecogTextElems, 300);
    i++;
  }, 800);
}
//  SECTION:============================================================= 
//            Main loop     
//  ===================================================================== 

// Get DOM elements to access
const divLatestRecogText = document.getElementById(config.idLatestRecogText);
const divLatestTranslated = document.getElementById(config.idLatestTranslated);
const divHistoryRecogText = document.getElementById(config.idHistoryRecogText);
const divHistoryTranslated = document.getElementById(config.idHistoryTranslated);
const divTranslated = document.getElementById(config.idTranslatedContainer);
// const { textNode: newOriginaltextNode, dots: dots } = appendTextNodeEtcToNewOriginal();

const finalSpan = document.getElementById(config.idLatestRecogFinal);
const interimSpan = document.getElementById(config.idLatestRecogInterim);
finalSpan.textContent = '';
interimSpan.textContent = '';
const finalSpanOrigOpacity = getElemOpacity(finalSpan);
const interimSpanOrigOpacity = getElemOpacity(interimSpan);

const arrayHistoryRecogTexts = [];
const arrayHistoryRecogTextElems = [];


createHistoryElements(divHistoryRecogText, arrayHistoryRecogTextElems, MAX_HISTORY_LENGTH);


// // If translated text is not used, remove it.
// if (!config.showTranslated) {
//   hideElem(divTranslated);
// }

// Instantiate Websocket client.
const wsclient = new WSClient({ url: config.urlObsSpeechOverlayWs, onMessage, onClose, onError });




// testShowMesasgeOriginals();
// testShowMesasgeTranslated();
