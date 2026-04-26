export type PcmAudioChunk = {
  seq: number;
  sampleRate: number;
  mimeType: "audio/pcm;rate=16000";
  data: string;
  byteLength: number;
  durationMs: number;
};

export type MicRecorder = {
  stop: () => void;
};

type CreateMicRecorderOptions = {
  chunkMs?: number;
  onChunk: (chunk: PcmAudioChunk) => void;
};

const TARGET_SAMPLE_RATE = 16000;
const DEFAULT_CHUNK_MS = 250;

const arrayBufferToBase64 = (buffer: ArrayBuffer) => {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return window.btoa(binary);
};

const downsample = (
  input: Float32Array,
  inputSampleRate: number,
  targetSampleRate: number,
) => {
  if (targetSampleRate === inputSampleRate) {
    return input;
  }

  const ratio = inputSampleRate / targetSampleRate;
  const outputLength = Math.floor(input.length / ratio);
  const output = new Float32Array(outputLength);

  for (let outputIndex = 0; outputIndex < outputLength; outputIndex += 1) {
    const inputIndex = Math.floor(outputIndex * ratio);
    output[outputIndex] = input[inputIndex] ?? 0;
  }

  return output;
};

const floatToPcm16 = (input: Float32Array) => {
  const buffer = new ArrayBuffer(input.length * 2);
  const view = new DataView(buffer);

  input.forEach((sample, index) => {
    const clamped = Math.max(-1, Math.min(1, sample));
    view.setInt16(
      index * 2,
      clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff,
      true,
    );
  });

  return buffer;
};

export const createPcm16MicRecorder = async ({
  chunkMs = DEFAULT_CHUNK_MS,
  onChunk,
}: CreateMicRecorderOptions): Promise<MicRecorder> => {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
    },
  });
  const audioWindow = window as Window &
    typeof globalThis & {
      webkitAudioContext?: typeof AudioContext;
    };
  const AudioContextClass =
    audioWindow.AudioContext ?? audioWindow.webkitAudioContext;

  if (!AudioContextClass) {
    stream.getTracks().forEach((track) => track.stop());
    throw new Error("AudioContext is not available in this browser.");
  }

  const audioContext = new AudioContextClass();
  const source = audioContext.createMediaStreamSource(stream);
  const processor = audioContext.createScriptProcessor(4096, 1, 1);
  const samplesPerChunk = Math.round((TARGET_SAMPLE_RATE * chunkMs) / 1000);
  let pendingSamples: number[] = [];
  let seq = 0;

  processor.onaudioprocess = (event) => {
    const input = event.inputBuffer.getChannelData(0);
    const downsampled = downsample(
      input,
      audioContext.sampleRate,
      TARGET_SAMPLE_RATE,
    );
    for (let index = 0; index < downsampled.length; index += 1) {
      pendingSamples.push(downsampled[index] ?? 0);
    }

    while (pendingSamples.length >= samplesPerChunk) {
      const chunkSamples = pendingSamples.slice(0, samplesPerChunk);
      pendingSamples = pendingSamples.slice(samplesPerChunk);
      const pcmBuffer = floatToPcm16(Float32Array.from(chunkSamples));

      onChunk({
        seq,
        sampleRate: TARGET_SAMPLE_RATE,
        mimeType: "audio/pcm;rate=16000",
        data: arrayBufferToBase64(pcmBuffer),
        byteLength: pcmBuffer.byteLength,
        durationMs: chunkMs,
      });
      seq += 1;
    }
  };

  source.connect(processor);
  processor.connect(audioContext.destination);

  return {
    stop: () => {
      processor.disconnect();
      source.disconnect();
      stream.getTracks().forEach((track) => track.stop());
      void audioContext.close();
    },
  };
};
