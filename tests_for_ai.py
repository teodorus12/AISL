import os
import numpy as np
import audio_recognition as ar

MODEL_PATH  = "ai6.pkl"
TEST_FOLDER = "testing_data"


def get_label_from_filename(filename: str) -> str:
    return os.path.splitext(filename)[0].split("_test")[0]


def test_audio_ai() -> None:
    nn   = ar.NeuralNetwork.load(MODEL_PATH)
    proc = ar.AudioProcessor()

    correct = 0
    total   = 0

    for file in sorted(os.listdir(TEST_FOLDER)):
        if not file.endswith(".wav"):
            continue

        path = os.path.join(TEST_FOLDER, file)

        vec  = proc.wav_to_vector(path)
        out  = nn.forward(vec)

        pred = nn.labels[np.argmax(out)]
        true = get_label_from_filename(file)

        status = "✓" if pred == true else "✗"
        print(f"{status}  {file:<30}  pred={pred:<12}  true={true}")

        correct += int(pred == true)
        total   += 1

    if total == 0:
        print("No WAV files found in", TEST_FOLDER)
        return

    print(f"\nAccuracy: {correct}/{total}  ({correct / total * 100:.1f} %)")


if __name__ == "__main__":
    test_audio_ai()