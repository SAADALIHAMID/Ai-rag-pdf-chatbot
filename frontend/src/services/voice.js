/**
 * Zero-cost, 100% free Client-Side Voice Engine
 * Speech-to-Text (SpeechRecognition) + Text-to-Speech (SpeechSynthesis)
 */

class VoiceEngine {
  constructor() {
    this.recognition = null;
    this.isListening = false;
    this.synth = typeof window !== 'undefined' ? window.speechSynthesis : null;
    this.currentUtterance = null;
    this.voices = [];
    this.selectedVoice = null;
    this.isSpeaking = false;
    this.onSpeakingStateChange = null;

    try {
      this.initVoices();
    } catch (e) {
      console.warn("Error initializing voices:", e);
    }

    try {
      this.initRecognition();
    } catch (e) {
      console.warn("Error initializing speech recognition:", e);
    }
  }

  initVoices() {
    if (!this.synth) return;
    const load = () => {
      try {
        this.voices = this.synth.getVoices() || [];
        if (!Array.isArray(this.voices) || this.voices.length === 0) return;

        const preferred = this.voices.find((v) => {
          if (!v) return false;
          const name = v.name || "";
          const lang = v.lang || "";
          return name.includes("Natural") || name.includes("Google") || lang.startsWith("en");
        });

        this.selectedVoice = preferred || this.voices[0] || null;
      } catch (err) {
        console.warn("Could not load speech voices:", err);
      }
    };

    load();
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = load;
    }
  }

  initRecognition() {
    if (typeof window === 'undefined') return;
    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
      }
    } catch (err) {
      console.warn("SpeechRecognition not permitted or supported:", err);
      this.recognition = null;
    }
  }

  isSupported() {
    return {
      stt: !!(typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)),
      tts: !!(typeof window !== 'undefined' && window.speechSynthesis),
    };
  }

  startListening(onInterim, onFinal, onError) {
    if (!this.recognition) {
      try {
        this.initRecognition();
      } catch (e) {}
    }

    if (!this.recognition) {
      if (onError) onError(new Error("Speech recognition is not supported in this browser."));
      return;
    }

    if (this.isListening) {
      this.stopListening();
    }

    this.stopSpeaking();

    let finalTranscript = '';

    this.recognition.onstart = () => {
      this.isListening = true;
    };

    this.recognition.onresult = (event) => {
      let interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      if (onInterim) onInterim(interimTranscript || finalTranscript);
    };

    this.recognition.onerror = (event) => {
      this.isListening = false;
      if (event.error !== 'no-speech' && onError) {
        onError(event);
      }
    };

    this.recognition.onend = () => {
      this.isListening = false;
      if (onFinal) onFinal(finalTranscript.trim());
    };

    try {
      this.recognition.start();
    } catch (err) {
      console.warn("Recognition start failed or already active:", err);
    }
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      try {
        this.recognition.stop();
      } catch (e) {}
      this.isListening = false;
    }
  }

  speakText(text, onEnd) {
    if (!this.synth) return;

    this.stopSpeaking();

    try {
      const cleanText = (text || "")
        .replace(/【.*?】/g, '')
        .replace(/\[.*?\]/g, '')
        .replace(/[*_~`#]/g, '')
        .replace(/\n+/g, ' ')
        .trim();

      if (!cleanText) return;

      this.currentUtterance = new SpeechSynthesisUtterance(cleanText);
      if (this.selectedVoice) {
        this.currentUtterance.voice = this.selectedVoice;
      }
      this.currentUtterance.rate = 1.05;
      this.currentUtterance.pitch = 1.0;

      this.currentUtterance.onstart = () => {
        this.isSpeaking = true;
        if (this.onSpeakingStateChange) this.onSpeakingStateChange(true);
      };

      this.currentUtterance.onend = () => {
        this.isSpeaking = false;
        if (this.onSpeakingStateChange) this.onSpeakingStateChange(false);
        if (onEnd) onEnd();
      };

      this.currentUtterance.onerror = () => {
        this.isSpeaking = false;
        if (this.onSpeakingStateChange) this.onSpeakingStateChange(false);
      };

      this.synth.speak(this.currentUtterance);
    } catch (err) {
      console.warn("SpeechSynthesis error:", err);
      this.isSpeaking = false;
      if (this.onSpeakingStateChange) this.onSpeakingStateChange(false);
    }
  }

  stopSpeaking() {
    if (this.synth) {
      try {
        this.synth.cancel();
      } catch (e) {}
      this.isSpeaking = false;
      if (this.onSpeakingStateChange) this.onSpeakingStateChange(false);
    }
  }
}

export const voiceEngine = new VoiceEngine();
