import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal

fvz, sig = wavfile.read('LOG001.wav')

sig = sig.astype(np.float64)

sig = sig / (np.max(np.abs(sig)) + 1e-12)

N = 256

f, t, TFD = signal.spectrogram(sig,fs=fvz,window='hann',nperseg=N,noverlap=N // 2)

TFD_db = 10 * np.log10(TFD + 1e-12)

plt.figure(figsize=(10, 4))
plt.pcolormesh(t, f, TFD_db, shading='auto', cmap='viridis')
plt.ylim(0, 4000)
plt.colorbar()
plt.xlabel("čas (s)")
plt.ylabel("frekvenca (Hz)")
plt.show()