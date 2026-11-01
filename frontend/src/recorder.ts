export type Recording = { stop: () => Promise<Blob>; cancel: () => void };
export async function recordWav(): Promise<Recording> {
  if (!navigator.mediaDevices?.getUserMedia) throw new Error('Recording is unavailable in this browser. Type your answer instead.');
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
  const context = new AudioContext();
  const source = context.createMediaStreamSource(stream);
  const processor = context.createScriptProcessor(4096, 1, 1);
  const silence = context.createGain(); silence.gain.value = 0;
  const chunks: Float32Array[] = [];
  processor.onaudioprocess = event => chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
  source.connect(processor); processor.connect(silence); silence.connect(context.destination);
  let closed = false;
  const close = () => { if (closed) return; closed = true; source.disconnect(); processor.disconnect(); silence.disconnect(); stream.getTracks().forEach(track => track.stop()); void context.close(); };
  return {
    cancel: close,
    stop: async () => {
      const sampleRate = context.sampleRate; close();
      const size = chunks.reduce((n, chunk) => n + chunk.length, 0);
      if (!size) throw new Error('No audio was recorded. Try again or type your answer.');
      const buffer = new ArrayBuffer(44 + size * 2); const view = new DataView(buffer);
      const write = (offset: number, text: string) => [...text].forEach((char, i) => view.setUint8(offset + i, char.charCodeAt(0)));
      write(0, 'RIFF'); view.setUint32(4, 36 + size * 2, true); write(8, 'WAVE'); write(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true); view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true); write(36, 'data'); view.setUint32(40, size * 2, true);
      let offset = 44; for (const chunk of chunks) for (const value of chunk) { const sample = Math.max(-1, Math.min(1, value)); view.setInt16(offset, sample * (sample < 0 ? 32768 : 32767), true); offset += 2; }
      return new Blob([buffer], { type: 'audio/wav' });
    },
  };
}
