// Captures mic audio in the browser and downsamples it from the AudioContext rate
// (usually 48 kHz) to 16 kHz linear16 PCM, the format the Deepgram Voice Agent expects.
// Posts Int16 frames (~100 ms) to the main thread, which forwards them over the WebSocket.
class MicProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.outRate = 16000;
    this.ratio = sampleRate / this.outRate; // sampleRate is a global in the worklet scope
    this.frac = 0;        // fractional read index carried across render blocks
    this.out = [];        // accumulated Int16 samples
    this.flushSize = 1600; // ~100 ms at 16 kHz
  }

  process(inputs) {
    const input = inputs[0];
    if (input && input[0]) {
      const ch = input[0]; // Float32Array at `sampleRate`
      let i = this.frac;
      for (; i < ch.length; i += this.ratio) {
        let s = ch[Math.floor(i)] || 0;
        s = Math.max(-1, Math.min(1, s));
        this.out.push(s < 0 ? s * 0x8000 : s * 0x7fff);
      }
      this.frac = i - ch.length;

      if (this.out.length >= this.flushSize) {
        const frame = Int16Array.from(this.out);
        this.out.length = 0;
        this.port.postMessage(frame.buffer, [frame.buffer]);
      }
    }
    return true;
  }
}

registerProcessor("mic-processor", MicProcessor);
