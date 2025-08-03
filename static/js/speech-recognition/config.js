const defaultConfig = {
  languages: [
    { code: 'en-US', label: 'English' },
    { code: 'ja-JP', label: 'Japanese' },
  ],
  deafultLanguageCode: 'ja-JP',
  noSpeechTimeout: 2000, // ms
  // debounceTime: 300, // send recognitioin text  1/300msec 100-500msec is good
  throttleTime: 300,
  urlSpeechRecognitionWs: 'ws://localhost:8000/ws/speech-recognition',
};

export default defaultConfig;
