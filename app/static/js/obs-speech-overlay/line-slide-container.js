const cssRoot = document.querySelector(":root");
const cssRootStyle = getComputedStyle(cssRoot);
console.log(cssRootStyle.getPropertyValue("--line-order"));

const cssStyles = {
  lineHeight: cssRootStyle.getPropertyValue("--line-height"),
  newestLineHeight: cssRootStyle.getPropertyValue("--newest-line-height"),
  maxLines: cssRootStyle.getPropertyValue("--max-lines"),
  lineOrder: cssRootStyle.getPropertyValue("--line-order"),
  lineAlign: cssRootStyle.getPropertyValue("--line-align"),
  fontSize: cssRootStyle.getPropertyValue("--font-size"),
  fontColor: cssRootStyle.getPropertyValue("--font-color"),
  fontBgColor: cssRootStyle.getPropertyValue("--font-bg-color"),
  newestFontSize: cssRootStyle.getPropertyValue("--newest-font-size"),
  newestFontColor: cssRootStyle.getPropertyValue("--newest-font-color"),
  newestFontBgColor: cssRootStyle.getPropertyValue("--newest-font-bg-color"),
  sliderLineGap: cssRootStyle.getPropertyValue("--slider-line-gap"),
  padding: cssRootStyle.getPropertyValue("--padding"),
}


// Paste your TextSlider class here (with pushText and maxLength support)
export class TextSlider {
  constructor(parent, options = {}) {
    this.parent = typeof parent === "string" ? document.querySelector(parent) : parent;
    if (!(this.parent instanceof HTMLElement)) throw new Error("Invalid parent");

    this.maxLength = options.maxLength || cssStyles.maxLines;
    this.isAlignRight = options.isAlignRight || null;
    this.isUpward = options.isUpward || null;
    this.lastLine = null;
    this.isScrolled = true;
    this.lines = [];

    this.lineHeight = this._generateLineHeight(cssStyles.lineHeight);
    this.newestLineHeight = this._generateLineHeight(cssStyles.newestLineHeight);

    this.container = document.createElement("div");
    this.container.className = "text-slider-container";
    if (this.isAlignRight) {
      this.container.classList.add("align-right");
    }
    if (this.isUpward) {
      this.container.classList.add("upward");
    }
    this.parent.appendChild(this.container);

  }

  _pxToNum(pxStr) {
    return Number(pxStr.slice(0, -2));
  }

  // Generate line hight including padding and gap.
  _generateLineHeight(height) {
    return this._pxToNum(height) + 2 * this._pxToNum(cssStyles.padding) + this._pxToNum(cssStyles.sliderLineGap);
  }

  _updateNewestline(line) {
    if (this.lastLine) {
      this.lastLine.classList.remove("newest-line");
    }
    this.lastLine = line;
    this.lastLine.classList.add("newest-line");
  }

  _removeOldestLine() {
    const oldLine = this.lines[this.maxLength];
    oldLine.classList.add("fadeout");
    oldLine.addEventListener("transitionend", () => oldLine.remove(), { once: true });
    this._updatePositions();
    this.lines.splice(this.maxLength, 1);

  }

  _updatePositions() {
    this.lines.forEach((line, idx) => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          if (idx === 1) line.classList.remove("newest");
          line.style.transitionDelay = `${idx * 50}ms`;
          let direction = this.isUpward ? -1 : 1;
          if (idx === 0) {
            line.style.transform = `translateY(0)`;
          }
          else {
            line.style.transform = `translateY(${direction * ((idx - 1) * (this.lineHeight) + this.newestLineHeight)}px)`;
          }
        });
      });
    });
  }

  scrollOnly() {
    this.isScrolled = true;
    this.pushText("");
    console.debug("scroll only");
  }

  pushText(text) {
    // If last line is emptpy, push text to the last line.
    if (this.lastLine && this.lastLine.textContent === "") {
      const line = this.lastLine;
      line.textContent = text;
      this.isScrolled = false;
      if (text !== "") line.classList.add("show");
      return;
    }

    // Generarate line element for new comming text.
    const line = document.createElement("div");
    line.className = "text-slider-line newest";
    this.container.appendChild(line);
    this._updateNewestline(line);
    line.textContent = text;

    // if (!this.lineHeight) {
    //   this.lineHeight = line.offsetHeight || 30;
    // }

    this.lines.unshift(line);

    if (text !== "") {
      // text === "" means text slide only. If not, show.
      this.isScrolled = false;
      line.classList.add("show");
    }

    this._updatePositions();

    if (this.lines.length > this.maxLength) {
      this._removeOldestLine()
    }
  }

}


class InterimDisplay {
  constructor(parent, options = {}) {
    this.parent = typeof parent === "string" ? document.querySelector(parent) : parent;
    if (!(this.parent instanceof HTMLElement)) throw new Error("Invalid parent");

    this.isAlignRight = options.isAlignRight || null;
    this.isUpward = options.isUpward || null;

    this.interimDisplay = document.createElement("div");
    this.interimDisplay.className = "interim-display-container";
    if (this.isAlignRight) {
      this.interimDisplay.classList.add("align-right");
    }
    if (this.isUpward) {
      this.interimDisplay.classList.add("upward");
    }

    this.interimText = document.createElement("div");
    this.interimText.className = "interim-display-text";
    if (this.isAlignRight) {
    }
    this.interimText.textContent = "…"

    this.interimDisplay.appendChild(this.interimText);
    this.parent.appendChild(this.interimDisplay);
  }


  display(text) {
    this.interimText.classList.remove("hide");
    // this.interimText.addEventListener("transitionend", () => {
    //   this.interimText.classList.remove("hide");
    //   console.log("transitionend");
    // }, { once: true });

    // this.interimText.classList.add("hide");
    this.interimText.textContent = text;
    // this.interimText.classList.remove("hide");
  }

  hide() {
    this.interimText.classList.add("hide");
  }
}


export class RecogTextDisplay {
  constructor(parent, options = {}) {
    this.parent = typeof parent === "string" ? document.querySelector(parent) : parent;
    if (!(this.parent instanceof HTMLElement)) throw new Error("Invalid parent");

    this.isAlignRight = options.isAlignRight || false;
    this.isUpward = options.isUpward || false;
    this.maxLength = options.maxLength || cssStyles.maxLines;

    this.isFinal = false;
    this.recogText = null;
    this.recogTextDisplay = document.createElement("div");
    this.recogTextDisplay.className = "recog-display-container";
    this.parent.appendChild(this.recogTextDisplay);

    this.textHistoryDisplay = new TextSlider(this.recogTextDisplay, { isAlignRight: this.isAlignRight, isUpward: this.isUpward, });
    this.interimDisplay = new InterimDisplay(this.recogTextDisplay, { isAlignRight: this.isAlignRight, isUpward: this.isUpward });
  }

  displayMessage(message) {
    this._decodeMessage(message);
    if (this.isFinal) {
      console.log(this.isFinal);
      this.interimDisplay.hide();
      this.textHistoryDisplay.pushText(this.recogText);
    }
    else {
      if (!this.textHistoryDisplay.isScrolled) {
        this.textHistoryDisplay.scrollOnly();
      }
      this.interimDisplay.display(this.recogText);
    }
  }

  _decodeMessage(message) {
    this.isFinal = message.isFinal;
    this.recogText = message.recogText;
  }


}

// example
const messageExamples = [
  "hello",
  "how ",
  "how are ",
  "how are you?",
  "fine",
  "what time?",
  "see you next",
  "see you next week",
  "bye",
  "End",
];
const recogTextExamples = [
  // { recogText: "hello", isFinal: true },
  { recogText: "how", isFinal: false },
  { recogText: "how are", isFinal: false },
  { recogText: "how are you?", isFinal: true },
  { recogText: "I am", isFinal: false },
  { recogText: "I am fine", isFinal: false },
  { recogText: "日本語はどうでしょうか？", isFinal: true },
  { recogText: "I am fine. Thank you.", isFinal: true },
  { recogText: "I am fine. Thank you.", isFinal: true },
  { recogText: "I am fine. Thank you.", isFinal: true },
  // { recogText: "how are you?", isFinal: true },
];

function testInterimDisplay() {
  const interimDisplay = new InterimDisplay("#app");

  let i = 0;
  const timer = setInterval(() => {
    if (i === messageExamples.length) {
      interimDisplay.hide();
      clearInterval(timer);
      return;
    }
    interimDisplay.display(messageExamples[i]);
    i++;
  }, 500);
}


function testRecogTextDisplay() {
  const recogTextDisplay = new RecogTextDisplay("#app", { isAlignRight: true, isUpward: true });
  let i = 0;
  const timer = setInterval(() => {
    if (i === recogTextExamples.length) {
      clearInterval(timer);
      return;
    }
    recogTextDisplay.displayMessage(recogTextExamples[i]);
    i++;
  }, 500);
}



// testRecogTextDisplay();
