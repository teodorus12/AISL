import os
import numpy as np
import audio_recognition as ar


MODEL_PATH = "ai4.pkl"
TEST_FOLDER = "testing_data"


def get_label_from_filename(f):
    return os.path.splitext(f)[0].split("_test")[0]


def test_audio_ai():
    nn = ar.NeuralNetwork.load(MODEL_PATH)
    proc = ar.AudioProcessor()

    correct = 0
    total = 0

    for file in os.listdir(TEST_FOLDER):
        if not file.endswith(".wav"):
            continue

        path = os.path.join(TEST_FOLDER, file)

        vec = proc.wav_to_vector(path)
        vec = (vec - nn.mean) / nn.std

        out = nn.forward(vec)

        pred = nn.labels[np.argmax(out)]
        true = get_label_from_filename(file)

        print(file, "->", pred, "|", true)

        correct += (pred == true)
        total += 1

    if total == 0:
        print("No files found")
        return

    print("\nAccuracy:", correct / total * 100)


if __name__ == "__main__":
    test_audio_ai()