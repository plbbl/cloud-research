class CloudResearchPcmProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetRate = 16000;
    this.phase = 0;
    this.previous = 0;
  }

  process(inputs) {
    const input = inputs[0]?.[0];
    if (!input?.length) return true;

    let energy = 0;
    for (const sample of input) energy += sample * sample;
    const level = Math.sqrt(energy / input.length);

    const ratio = sampleRate / this.targetRate;
    const outputLength = Math.max(1, Math.floor((input.length - this.phase) / ratio));
    const pcm = new Int16Array(outputLength);
    let sourcePosition = this.phase;
    for (let index = 0; index < outputLength; index += 1) {
      const left = Math.floor(sourcePosition);
      const fraction = sourcePosition - left;
      const a = left < 0 ? this.previous : input[Math.min(left, input.length - 1)];
      const b = input[Math.min(left + 1, input.length - 1)];
      const sample = Math.max(-1, Math.min(1, a + (b - a) * fraction));
      pcm[index] = sample < 0 ? sample * 32768 : sample * 32767;
      sourcePosition += ratio;
    }
    this.phase = sourcePosition - input.length;
    this.previous = input[input.length - 1];
    this.port.postMessage({ pcm: pcm.buffer, level }, [pcm.buffer]);
    return true;
  }
}

registerProcessor("cloud-research-pcm", CloudResearchPcmProcessor);
