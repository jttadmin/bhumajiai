import io
import wave
import threading
import numpy as np
import sounddevice as sd

class MicrophoneRecorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.stream = None
        self.chunks = []
        self.lock = threading.Lock()

    def start(self):
        if self.stream is not None:
            raise RuntimeError('Already recording')
        self.chunks = []
        def callback(indata, frames, time_info, status):
            with self.lock:
                self.chunks.append(indata.copy())
        self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1,
                                     dtype='int16', callback=callback)
        try:
            self.stream.start()
        except Exception:
            self.stream.close()
            self.stream = None
            raise

    def stop(self):
        if self.stream is None:
            raise RuntimeError('Not recording')
        self.stream.stop()
        self.stream.close()
        self.stream = None
        with self.lock:
            samples = np.concatenate(self.chunks, axis=0) if self.chunks else np.empty((0, 1), dtype=np.int16)
        if len(samples) == 0:
            raise RuntimeError('No audio captured. Check microphone permissions.')
        out = io.BytesIO()
        with wave.open(out, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(samples.tobytes())
        out.seek(0)
        out.name = 'question.wav'
        return out
