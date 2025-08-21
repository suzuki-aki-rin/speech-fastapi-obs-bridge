// Module for communication with the server via WebSocket
export class WSClient {
  constructor({ url, onOpen, onMessage, onClose, onError } = {}) {
    if (!url) throw new Error('url is required');

    this.ws = new WebSocket(url);
    this.ws.onopen = () => { if (onOpen) onOpen(); };
    this.ws.onmessage = (e) => { if (onMessage) onMessage(e.data); };
    this.ws.onclose = () => { if (onClose) onClose(); };
    this.ws.onerror = (e) => { if (onError) onError(e); };
  }

  // Send a text message to the server
  send(message) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    }
    else {
      console.error("websocket is not open. cannot send.");
    }
  }
}


