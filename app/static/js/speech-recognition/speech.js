/**
 * SpeechRecognizer
 * ---------------
 * This class provides a wrapper around webkitSpeechRecognition, enabling speech-to-text with custom silence timeout.
 *
 * Core Features:
 * - Converts speech to text using the browser's Web Speech API.
 * - Allows setting a custom 'no speech' timeout: if no sound, speech, or result is detected for a specified number of milliseconds,
 *   the recognition session is auto-stopped and considered complete (i.e., a "short pause" closes recognition).
 * - Delivers recognized text—including intermediate ("interim") and finalized results—via callback.
 * - If recognition ends but interim text remains, it is treated as a final result and sent.
 *
 * Usage Example:
 * const recognizer = new SpeechRecognizer({
 *   lang: 'en-US',
 *   noSpeechMs: 2000, // 2 seconds
 *   onResult: (text, isFinal) => { ... },
 *   onError: (err) => { ... },
 *   onEnd: () => { ... }
 * });
 * recognizer.start();
 */


export class SpeechRecognizer {
  /**
   * @param {Object} handlers - Callback handlers and options
   * @param {string} [handlers.lang='ja-JP'] - Language code
   * @param {number} [handlers.noSpeechMs=2000] - Silence timeout in ms to force recognition end
   * @param {function} handlers.onResult - Function called as (text, isFinal)
   * @param {function} [handlers.onError] - Function called on recognition error
   * @param {function} [handlers.onEnd] - Function called when recognition ends
   */
  constructor({ lang = 'ja-JP', onResult, onError, onEnd, noSpeechMs = 2000 }) {
    if (!('webkitSpeechRecognition' in window)) {
      throw new Error('Webkit Speech Recognition is not supported in this browser');
    }
    // Core recognition object
    this.recognition = new webkitSpeechRecognition();
    this.recognition.lang = lang;
    this.recognition.interimResults = true;
    this.recognition.continuous = false; // continuous:true is unpredictable on Chrome

    this.latestInterim = '';   // Stores the latest interim transcript, if any
    this.noSpeechMs = noSpeechMs; // Custom user-defined silence timeout in ms
    this.silenceTimer = null;  // Timer reference for custom silence detection

    /**
     * Resets/starts the silence timer. If the specified time passes without speech/sound/result, stop recognition.
     */
    this._resetSilenceTimer = () => {
      if (this.silenceTimer) clearTimeout(this.silenceTimer);
      this.silenceTimer = setTimeout(() => {
        this.recognition.stop(); // Force stop after user-defined silence period
      }, this.noSpeechMs);
    };

    // When any sound is detected, reset the silence timer
    this.recognition.onsoundstart = () => {
      this._resetSilenceTimer();
    };

    // When voice activity is detected, reset the timer
    this.recognition.onspeechstart = () => {
      this._resetSilenceTimer();
    };

    // let lastTimestamp = 0; // To check onresult interval below
    /**
     * onresult delivers both interim (not yet finalized) and final recognition results
     */
    this.recognition.onresult = (event) => {
      // console.log(`onresult called: resultIndex=${event.resultIndex}, total results=${event.results.length}`);
      //
      // // Check onresult() interval
      // const now = Date.now();
      //
      // if (lastTimestamp !== 0) {
      //   const interval = now - lastTimestamp;
      //   console.log(`onresult event interval: ${interval} ms`);
      // } else {
      //   console.log('onresult event first fired');
      // }
      // lastTimestamp = now;
      // // Check onresult interval end

      for (let i = event.resultIndex; i < event.results.length; i++) {
        let result = event.results[i];
        let recogText = result[0].transcript;
        let isFinal = result.isFinal;
        // console.log(`result[${i}]: recogText="${recogText}", isFinal=${isFinal}`);
        if (onResult) {
          onResult(recogText, isFinal);
        }
        if (isFinal) {
          this.latestInterim = ''; // Intermediate buffer is cleared when finalized
        } else {
          this.latestInterim = recogText; // Store the latest interim transcript
        }
      }
      this._resetSilenceTimer(); // Receiving a result, reset timer
    };

    /**
     * Forward any error to the supplied handler
     */
    this.recognition.onerror = (event) => {
      if (event.error === 'no-speech') {
        // On no-speech error, stop recognition, but do NOT show alert or call onError
        this.recognition.stop();
        return; // Simply exit the handler
      }
      // For all other errors, call the error handler (could show alert)
      if (onError) onError(event.error);
    };

    /**
     * onend fires when recognition session closes (detected silence, error, manual stop, etc.)
     * If there was still an interim transcript, treat it as a final result before ending.
     */
    this.recognition.onend = () => {
      // Cancel the silence timer
      if (this.silenceTimer) clearTimeout(this.silenceTimer);
      // Flush out any unfinished interim result as a final result (due to silence/end)
      if (this.latestInterim) {
        onResult(this.latestInterim, true);
        this.latestInterim = '';
      }
      if (onEnd) onEnd();
    };
  }

  setLanguage(lang) {
    this.recognition.lang = lang;
  }
  getLanguage() {
    return this.recognition.lang;
  }

  /**
   * Start recognition.
   */
  start() { this.recognition.start(); }

  /**
   * Stop recognition early.
   */
  stop() { this.recognition.stop(); }
}
