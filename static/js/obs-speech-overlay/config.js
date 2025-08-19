const defaultConfig = {
  urlObsSpeechOverlayWs: 'ws://localhost:8000/ws/obs-speech-overlay',
  eraseTimeMsec: 3000, // ms
  showTranslated: true,

  idLatestRecogText: 'latest-recog-text',
  idLatestRecogFinal: 'latest-recog-final',
  idLatestRecogInterim: 'latest-recog-interim',
  idHistoryRecogText: 'history-recog-text',

  idTranslatedContainer: 'translated-subtitle',
  idLatestTranslated: 'latest-translated-text',
  idHistoryTranslated: 'history-translated',
  heartbeat: 'heartbeat',
};

export default defaultConfig;
