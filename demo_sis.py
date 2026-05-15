"""
Demonstracija: branje LOG*.BIN, dekodiranje (SPO), sestavi_podatke, grafi za vse IMU kanale.
Zvok (chunk id 4) se bere iz LOG004.BIN v mapi te skripte (ne glede na pot IMU datoteke).
"""

from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

from create_packets_final import CREATE_PACKETS
from sis_obdelava import (
    LOCLJIVOST_ACC_MPS2,
    LOCLJIVOST_GYRO_DPS,
    LOCLJIVOST_MAG_G,
    SPO_CHUNK_ID_OPIS,
    sestavi_podatke,
    prikazi_signal,
)

NASTAVLJENA_FVZ_HZ = 100.0
NASTAVLJENA_FVZ_ZVOK_HZ = 8000.0
IME_DATOTEKE_ZVOK = "LOG004.BIN"

TRAJANJE_POVECAVA_S = 2.5

ZVOK_POVECAVA_T0_S = 0.1
ZVOK_POVECAVA_T1_S = 0.7

KANALI_IMU: tuple[tuple[int, float, str, str, str], ...] = (
    (1, LOCLJIVOST_ACC_MPS2, "m/s²", "posp", SPO_CHUNK_ID_OPIS[1] + " (X, Y, Z)"),
    (2, LOCLJIVOST_GYRO_DPS, "°/s", "gyro", SPO_CHUNK_ID_OPIS[2] + " (X, Y, Z)"),
    (3, LOCLJIVOST_MAG_G, "G", "mag", SPO_CHUNK_ID_OPIS[3] + " (X, Y, Z)"),
)

# Funkcija za izbiro prikaza povecave dogodka
def _izberi_okno_dogodka(signal: np.ndarray, fvz: float, sirina_s: float) -> tuple[int, int]:
    # Najde okno dolžine sirina_s z največjo spremembo magnitude (1D: |x|, večdimenzijsko: ||·||).
    n = signal.shape[0]
    w = max(3, int(fvz * sirina_s))
    if n <= w or not np.isfinite(fvz) or fvz <= 0:
        return 0, n
    if signal.ndim == 1: #1D 
        mag = np.abs(signal.astype(np.float64, copy=False))
    else:
        mag = np.linalg.norm(signal, axis=1)
    best_i = 0
    best_score = -1.0
    for i in range(0, n - w): 
        s = float(np.max(mag[i : i + w]) - np.min(mag[i : i + w])) # izbira okna z najvecjo razliko
        if s > best_score:
            best_score = s
            best_i = i
    return best_i, min(best_i + w, n)


def _prikazi_kanal(
    imu_paketi: list,
    tip: int,
    lsb: float,
    enota: str,
    kratko: str,
    opis: str,
) -> None:
    # Za en senzor: celoten signal + interval z največjo spremembo magnitude.
    fvz, signal = sestavi_podatke(imu_paketi, tip=tip, locijivost_po_lsb=lsb)
    print(f"  id={tip} ({kratko}): Fvz = {fvz:.3f} Hz, vzorcev = {signal.shape[0]}, oblika {signal.shape}")
    # filtrira po id, sestavi N x 3 signal, izracuna fvz
    naslov1 = (
        f"Celoten signal — {opis}\n"
        f"Fvz (izmerjena) = {fvz:.2f} Hz | nastavljena ≈ {NASTAVLJENA_FVZ_HZ:.0f} Hz | enote: {enota}"
    )
    prikazi_signal(
        signal,
        naslov=naslov1,
        fvz=fvz,
        oznake_kanalov=("X", "Y", "Z"),
        enota_y=enota,
        ime_figure=f"{kratko}_celoten",
    )
    # povecan graf
    s, e = _izberi_okno_dogodka(signal, fvz, TRAJANJE_POVECAVA_S)
    if np.isfinite(fvz) and fvz > 0:
        t0, t1 = s / fvz, e / fvz
        cas_oznaka = f"Interval [{t0:.2f} s, {t1:.2f} s]"
    else:
        cas_oznaka = f"Indeksi [{s}, {e})"
    naslov2 = (
        f"Povečava ~{TRAJANJE_POVECAVA_S:.1f} s — {opis}\n"
        f"{cas_oznaka} | Fvz = {fvz:.2f} Hz"
    )
    prikazi_signal(
        signal,
        naslov=naslov2,
        startInd=s,
        endInd=e,
        fvz=fvz if np.isfinite(fvz) and fvz > 0 else None,
        oznake_kanalov=("X", "Y", "Z"),
        enota_y=enota,
        ime_figure=f"{kratko}_interval",
    )


def _sestavi_zvocni_tok(paketi: list) -> tuple[float, np.ndarray]:
    
    # Zloži vse pakete z id=4 v en 1D signal in oceni Fvz (povp. št. vzorcev / povp. Δt med paketi).
    aud = [p for p in paketi if p.get("id") == 4]
    if not aud:
        return float("nan"), np.array([], dtype=np.float64)

    tpaketi: list[float] = []
    nvz: list[int] = []
    for i in range(len(aud) - 1):
        dt = float(aud[i + 1]["ts"]) - float(aud[i]["ts"]) # casovni zig za racunanje fvz
        if dt <= 0:
            continue
        tpaketi.append(dt)
        nvz.append(int(np.asarray(aud[i]["data"]).size))

    if tpaketi:
        fvz = float(np.mean(nvz) / np.mean(tpaketi))
    else:
        fvz = float("nan")

    deli = [np.asarray(p["data"], dtype=np.float64).ravel() for p in aud]
    signal = np.concatenate(deli) if deli else np.array([], dtype=np.float64)
    return fvz, signal


def _prikazi_zvok(pot_datoteke: str) -> None:
    paketi = CREATE_PACKETS(pot_datoteke)
    fvz, signal = _sestavi_zvocni_tok(paketi)
    if signal.size == 0:
        print(f"  Zvok ({os.path.basename(pot_datoteke)}): ni paketov z id=4.")
        return

    print(
        f"  Zvok ({os.path.basename(pot_datoteke)}): Fvz = {fvz:.2f} Hz, "
        f"vzorcev = {signal.size}"
    )

    naslov1 = (
        f"Celoten signal — zvok (A-law → int16), datoteka {os.path.basename(pot_datoteke)}\n"
        f"Fvz (izmerjena) = {fvz:.2f} Hz | nastavljena ≈ {NASTAVLJENA_FVZ_ZVOK_HZ:.0f} Hz"
    )
    prikazi_signal(
        signal,
        naslov=naslov1,
        fvz=fvz,
        enota_y="vrednost vzorca (int16)",
        ime_figure="zvok_celoten",
    )
    # povecan graf zvoka
    if np.isfinite(fvz) and fvz > 0:
        s = int(np.floor(ZVOK_POVECAVA_T0_S * fvz))
        e = int(np.ceil(ZVOK_POVECAVA_T1_S * fvz))
        s = max(0, min(s, signal.size))
        e = max(s + 1, min(e, signal.size))
        cas_oznaka = (
            f"Interval {ZVOK_POVECAVA_T0_S * 1000:.0f} ms – {ZVOK_POVECAVA_T1_S * 1000:.0f} ms "
            f"(indeksi [{s}, {e}))"
        )
    else:
        s, e = 0, min(signal.size, 1)
        cas_oznaka = f"Indeksi [{s}, {e}) (Fvz ni znan)"
    naslov2 = (
        f"Povečava zvoka: {ZVOK_POVECAVA_T0_S * 1000:.0f} ms – {ZVOK_POVECAVA_T1_S * 1000:.0f} ms\n"
        f"{cas_oznaka} | Fvz = {fvz:.2f} Hz"
    )
    prikazi_signal(
        signal,
        naslov=naslov2,
        startInd=s,
        endInd=e,
        fvz=fvz if np.isfinite(fvz) and fvz > 0 else None,
        enota_y="vrednost vzorca (int16)",
        ime_figure="zvok_interval",
    )


def main() -> None:
    base = os.path.dirname(os.path.abspath(__file__))
    pot = os.path.join(base, "LOG011.BIN")
    if len(sys.argv) > 1:
        pot = sys.argv[1]

    pot_zvok = os.path.join(base, IME_DATOTEKE_ZVOK)

    samo_tip: int | None = None
    if len(sys.argv) > 2:
        try:
            samo_tip = int(sys.argv[2])
        except ValueError:
            print("Drugi argument mora biti 1, 2 ali 3 (samo ta senzor).")
            sys.exit(1)
        if samo_tip not in (1, 2, 3):
            print("Drugi argument mora biti 1, 2 ali 3.")
            sys.exit(1)

    if not os.path.isfile(pot):
        print(f"Datoteka ne obstaja: {pot}")
        sys.exit(1)

    paketi = CREATE_PACKETS(pot)
    imu = [p for p in paketi if p.get("id") in (1, 2, 3)]
    if not imu:
        print("V datoteki ni IMU paketov (id 1–3).")
        sys.exit(1)

    kanali = [k for k in KANALI_IMU if samo_tip is None or k[0] == samo_tip]
    print(f"Datoteka: {pot}")
    print("Senzorji:" if samo_tip is None else f"Samo senzor id={samo_tip}:")
    for tip, lsb, enota, kratko, opis in kanali:
        st = sum(1 for p in imu if p.get("id") == tip)
        if st == 0:
            print(f"  id={tip} ({kratko}): ni paketov — preskočeno.")
            continue
        _prikazi_kanal(imu, tip, lsb, enota, kratko, opis)

    if os.path.isfile(pot_zvok):
        print(f"Zvok (vedno iz {IME_DATOTEKE_ZVOK}):")
        _prikazi_zvok(pot_zvok)
    else:
        print(
            f"Zvok: datoteka {pot_zvok} ne obstaja — preskočeno "
            f"(dodaj {IME_DATOTEKE_ZVOK} v mapo skripte)."
        )

    plt.show()


if __name__ == "__main__":
    main()
