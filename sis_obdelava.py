"""
SIS — sestavljanje paketov DataLoggerja v signal (N×3) in prikaz.

Časovna značka iz CREATE_PACKETS je v sekundah (izvirno uint32 ms / 1000).
Število zlogov na koordinato po tipu podatkov (id); za int16 = 2 zloga.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Union

import numpy as np
import matplotlib.pyplot as plt

PaketVhod = Union[Mapping[str, Any], "Paket"]


SPO_CHUNK_ID_OPIS: dict[int, str] = {
    1: "pospeškometer (ACC)",
    2: "žiroskop (GYRO)",
    3: "magnetometer (MAG)",
    4: "zvok (A-law)",
}

LOCLJIVOST_ACC_MPS2 = 6.125e-5 * 9.81  # m/s² na LSB
LOCLJIVOST_GYRO_DPS = 8.75e-3  # °/s na LSB
LOCLJIVOST_MAG_G = 1.5e-3  # Gauss na LSB (npr. 0,5 G ≈ 50 µT)

LOCLJIVOST_LSB_PO_ID: dict[int, float] = {
    1: LOCLJIVOST_ACC_MPS2,
    2: LOCLJIVOST_GYRO_DPS,
    3: LOCLJIVOST_MAG_G,
}

# Število bajtov na eno koordinato (X, Y ali Z) glede na tip; pri int16 je 2.
ZLOGI_NA_KOORDINATO: dict[int, int] = {
    1: 2,
    2: 2,
    3: 2,
}


@dataclass
class Paket:
    id: int
    ts: float
    data: np.ndarray


def _p_id(p: PaketVhod) -> int:
    if isinstance(p, Paket):
        return p.id
    return int(p["id"])


def _p_ts(p: PaketVhod) -> float:
    if isinstance(p, Paket):
        return float(p.ts)
    return float(p["ts"])


def _p_data(p: PaketVhod) -> np.ndarray:
    if isinstance(p, Paket):
        return p.data
    return p["data"]


def zlogi_za_tip(tip_id: int) -> int:
    if tip_id not in ZLOGI_NA_KOORDINATO:
        raise KeyError(
            f"Neznan tip podatkov id={tip_id}. Dodaj ga v ZLOGI_NA_KOORDINATO."
        )
    return ZLOGI_NA_KOORDINATO[tip_id]

# pretvori numpy v unit8 pogled
def _as_uint8_view(data: np.ndarray) -> np.ndarray:
    arr = np.asarray(data)
    if arr.dtype == np.uint8:
        return arr.ravel()
    if not arr.flags["C_CONTIGUOUS"]:
        arr = np.ascontiguousarray(arr)
    return arr.view(np.uint8).ravel()


def _stevilo_vzorcev_iz_paketa(tip_id: int, data: np.ndarray) -> int:
    z = zlogi_za_tip(tip_id)
    u8 = _as_uint8_view(data)
    b_na_vzorec = 3 * z
    if u8.size % b_na_vzorec != 0:
        raise ValueError(
            f"Dolžina payloada ({u8.size} B) ni večkratnik 3·zlogi ({b_na_vzorec}) za id={tip_id}."
        )
    return u8.size // b_na_vzorec

# pretvori surove bajte/int16 v (N, 3)
def _data_v_matriko_xyz(tip_id: int, data: np.ndarray) -> np.ndarray:
    """Pretvori surove bajte/int16 v (N, 3)."""
    z = zlogi_za_tip(tip_id)
    u8 = _as_uint8_view(data)
    n = _stevilo_vzorcev_iz_paketa(tip_id, data)
    raw = u8[: n * 3 * z].tobytes()
    if z == 2:
        v = np.frombuffer(raw, dtype="<i2").reshape(n, 3).astype(np.float64)
        return v
    if z == 4:
        v = np.frombuffer(raw, dtype="<i4").reshape(n, 3).astype(np.float64)
        return v
    raise NotImplementedError(f"Zlogi={z} na koordinato še niso podprti.")


def sestavi_podatke(
    seznam_paketov: Sequence[PaketVhod],
    tip: int | None = None,
    locijivost_po_lsb: float | None = None,
) -> tuple[float, np.ndarray]:
    """
    Izračuna povprečno vzorčevalno frekvenco Fvz (Hz) in zloži vse vzorce v matriko (N, 3).

    Uporabi samo pakete z izbranim ``tip`` (id). Če ``tip`` manjka, vzame id prvega paketa.

    ``locijivost_po_lsb``: če podano, pomnoži vse komponente (fizikalna enota na LSB).
    """
    if not seznam_paketov:
        raise ValueError("seznam_paketov je prazen.")

    if tip is None:
        tip = _p_id(seznam_paketov[0])

    filtrirani = [p for p in seznam_paketov if _p_id(p) == tip]
    if not filtrirani:
        raise ValueError(f"Ni paketov s tipom id={tip}.")

    tpaketi: list[float] = [] # casovni interval med paketi
    nvz: list[int] = [] #st vzorcev v paketu
    for i in range(len(filtrirani) - 1):
        dt = _p_ts(filtrirani[i + 1]) - _p_ts(filtrirani[i])
        if dt <= 0:
            continue
        tpaketi.append(dt)
        nvz.append(_stevilo_vzorcev_iz_paketa(tip, _p_data(filtrirani[i])))

    if tpaketi:
        avg_t = float(np.mean(tpaketi))
        avg_n = float(np.mean(nvz))
        fvz = avg_n / avg_t
    else:
        # En sam paket — ocena iz časovnega obsega ni možna
        fvz = float("nan")

    bloki = [_data_v_matriko_xyz(tip, _p_data(p)) for p in filtrirani] # pretvori v matriko (N, 3)
    matrika = np.vstack(bloki)

    if locijivost_po_lsb is not None:
        matrika = matrika * float(locijivost_po_lsb)

    return fvz, matrika


def prikazi_signal(
    signal: np.ndarray,
    naslov: str | None = None,
    startInd: int | None = None,
    endInd: int | None = None,
    *,
    fvz: float | None = None,
    oznake_kanalov: Sequence[str] | None = None,
    enota_y: str = "",
    casovna_os: str = "čas",
    ime_figure: str | int | None = None,
) -> None:
    """
    Nariše signal: 1D vektor ali večstolpčna matrika (npr. X, Y, Z).

    Če sta ``startInd``/``endInd`` podana, se prikaže interval [startInd, endInd) po prvi dimenziji.
    ``fvz``: vzorčevalna frekvenca za časovno os v sekundah; če manjka, os je indeks vzorca.
    """
    sig = np.asarray(signal) #normalizira tip
    a = int(startInd) if startInd is not None else 0 
    b = int(endInd) if endInd is not None else sig.shape[0]
    a = max(0, a)
    b = min(sig.shape[0], b)
    if b <= a:
        raise ValueError(f"Neveljaven interval: startInd={startInd}, endInd={endInd}")

    kos = sig[a:b, ...] if sig.ndim > 1 else sig[a:b]
    #ustvarjanje grafa
    if ime_figure is not None:
        fig, ax = plt.subplots(num=ime_figure, figsize=(10, 5))
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
    n = kos.shape[0]
    if fvz is not None and fvz > 0:
        t = (a + np.arange(n)) / fvz
        xlabel = f"{casovna_os} (s)"
    else:
        t = a + np.arange(n)
        xlabel = "indeks vzorca"
    # 1d v več d signal
    if kos.ndim == 1:
        ax.plot(t, kos, linewidth=0.8)
        if enota_y:
            ax.set_ylabel(enota_y)
    else: # več d signal
        nkan = kos.shape[1]
        if oznake_kanalov is None:
            oznake_kanalov = [f"kanal {k}" for k in range(nkan)]
        for k in range(nkan):
            ax.plot(t, kos[:, k], linewidth=0.8, label=str(oznake_kanalov[k]))
        ax.legend(loc="upper right")
        ylab = " / ".join(str(x) for x in oznake_kanalov)
        if enota_y:
            ylab = f"{ylab} ({enota_y})"
        ax.set_ylabel(ylab)
    ax.set_xlabel(xlabel)
    ax.grid(True, alpha=0.3)
    if naslov:
        ax.set_title(naslov)
    fig.tight_layout()
    plt.show(block=False)
