from convert_bin_to_wav import collect_inputs, convert_file
from pathlib import Path


WAV_OUTPUT_DIR = "wav_out"
BIN_INPUT = "bin_folder"

def convert_all_bin_in_cwd() -> None:
    bin_folder = Path(BIN_INPUT)

    if not bin_folder.exists():
        print("Mapa 'bin_folder' ne obstaja.")
        return

    if not bin_folder.is_dir():
        print("'bin_folder' ni mapa.")
        return

    bin_files = collect_inputs([str(bin_folder)])

    if not bin_files:
        print("Ni BIN datotek v mapi bin_folder.")
        return

    output_dir = Path(WAV_OUTPUT_DIR)
    failures = 0

    for bin_file in bin_files:
        try:
            convert_file(bin_file, output_dir, sample_rate=None)
        except Exception as exc:
            failures += 1
            print(f"[ERR] {bin_file.name}: {exc}")

    if failures:
        print(f"Končano z {failures} napako/ami.")
    else:
        print(f"Vse BIN datoteke pretvorjene v {output_dir.resolve()}/")