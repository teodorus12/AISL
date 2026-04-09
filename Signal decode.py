import numpy as np
import matplotlib as Mplt
import matplotlib.pyplot as pplt
import pickle


#generira signal
def generiraj_signal (cas : float, frekvenca_tona : float) -> np.ndarray:
    
    num_vzorcev = int(cas * 800)
    
    time_vec = np.arange(num_vzorcev) / 800
    
    max_V = (2 ** 12) // 2-1
    
    signal = max_V * np.sin(2 * np.pi * frekvenca_tona * time_vec)
    signal = np.round(signal).astype(np.int16)
    signal = signal.reshape(-1, 1)
    return signal

#sama funkcija pove kaj počne
def sestavi_podatke (input_file):
            
    seznamPodatkov = []
    
    with open(input_file, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            deli = line.split(";")

            packet_id = int(deli[0])
            ts = float(deli[1])

            data = np.array(
                list(map(int, deli[2].split(","))),
                dtype=np.int16
            ).reshape(-1, 1)

            seznamPodatkov.append([packet_id, ts, data])

    if len(seznamPodatkov) < 2:
        raise ValueError("Premalo paketov oz. ni podanih paketov.")
    
    signali = []
    TPaketi = []
    vsi_Nvz = []
    
    for i in range(len(seznamPodatkov)):
        paket = seznamPodatkov[i]
        
        id = paket[0]
        ts = paket[1]
        data = paket[2]
        data = data.reshape(-1,1)
        signali.append(data)
        
        Nvz = data.shape[0]
        vsi_Nvz.append(Nvz)
        
        if i > 0:
            prev_ts = seznamPodatkov[i-1][1]
            difT = ts - prev_ts
            TPaketi.append(difT)
        
    TPaketAVG = np.mean(TPaketi)
    NvzAVG = np.mean(vsi_Nvz)
    Fvz = NvzAVG / TPaketAVG
    Fvz = 10
    signal = np.vstack(signali)
        
    return Fvz, signal

def prikazi_signal(signal: np.ndarray, naslov: str = "", startInd: int = None, endInd: int = None):
    if startInd is None:
        startInd = 0
    if endInd is None:
        endInd = len(signal)   
        
    odsek_prikazanega_signala = signal[startInd:endInd]
    pplt.figure()
    
    pplt.plot(odsek_prikazanega_signala)
    pplt.ylabel("amplituda")
    pplt.xlabel("Vzorec")
    if naslov == "":
        naslov = "No input name"
    pplt.title(naslov)
    pplt.grid(True)
    pplt.show()
    

#main
if __name__ == '__main__':
    Fvz, signal = sestavi_podatke("packets.txt")
    
    prikazi_signal(
        signal, naslov =
        f"Signal z frekvenco {Fvz:.3f}Hz"
    )
    prikazi_signal(
        signal, naslov =
        f"Signal z frekvenco {Fvz:.3f}Hz",
        startInd=2,
        endInd= int(Fvz * 2)
    )
    
    