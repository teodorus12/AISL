# AISL — AI Sign Language Interpreter

AISL (Artificial Intelligence Sign Language) is a project that uses AI to:
-  Interpret **sign language from video input**
-  Convert **spoken words into ASL gesture images**

The goal is to bridge communication by combining computer vision and speech processing.

---

##  Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/teodorus12/AISL.git
cd AISL
```

### 2. Switch to the development branch
```bash
git checkout dev
git pull
```

### 3. Create a feature branch
Use a clear naming convention:
```bash
git checkout -b feature/<ID>-<short-description>
git push -u origin feature/<ID>-<short-description>
```

### 4. Commit and push your changes
```bash
git add .
git commit -m "feat: short description of changes"
git push
```

---

##  Contributing Guidelines

- Keep commits small and focused  
- Use clear commit messages (`feat:`, `fix:`, `docs:`)  
- Always branch from `dev`  
- Open a Pull Request when your feature is ready  

---

## 🔌 Hardware Setup

### STM32 Connection
- Connect using:
  - **USB Micro**
  - **USB Mini**
- Both cables must support **data transfer** (not just charging)

---

##  Serial Monitoring (PuTTY)

PuTTY is optional but recommended for debugging and monitoring.

### Download
https://putty.org

### Configuration

| Setting            | Value          |
|--------------------|---------------|
| Serial line        | COM5 (varies) |
| Speed (baud rate)  | 9600          |
| Connection type    | Serial        |

### Additional Settings
- **Logging** → All session output  
- **Terminal** → Local echo → Force on  

Save the session to avoid repeating setup.

---

## Testing the Connection

1. Open PuTTY  
2. Start the serial connection  
3. Run the command:
```bash
STREAM
```

 If you see a continuous stream of data, the connection is working.

---

##  Running the Application

### Python setup (Windows)

1. Open **Command Prompt** or **PowerShell** in the project folder.
2. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install numpy pyserial matplotlib librosa opencv-python mediapipe tkinter
```

4. Start the main menu:

```bash
python main.py
```

### Audio recognition GUI (optional)

To train or test the audio model separately:

```bash
.venv\Scripts\activate
python audio_recognition.py
```

Use **Load** and select `ai1.0.pkl` for a pre-trained model.

---

##  Console Menu

The main program (`main.py`) provides the following options:

| Option | Description |
|--------|-------------|
| **0** | HELP — show menu |
| **1** | Download a BIN file from the device → `bin_folder/` |
| **2** | Parse a BIN file into packets → `packets.txt` |
| **3** | Stream data from serial port → `stream.bin` |
| **4** | List files on the device |
| **5** | Clear in-memory chunks |
| **6** | Build signal from `packets.txt` |
| **7** | Plot signal (matplotlib) |
| **8** | Convert all BIN files in `bin_folder/` to WAV → `wav_out/` |
| **9** | Exit |
| **10**| Download BIN and convert to WAV by category (kava, pivo, čaj, sok, viski) |
| **11**| Recognize word from `testing_data/` and play sign videos from `signs_data/` |

**Option 11:** choose a test WAV file → the AI predicts the word (e.g. *čaj*) → sign videos play in letter order (e.g. Č → A → J). Press **q** to skip the current video.

---

##  Project Data

| Folder / file | Description |
|---------------|-------------|
| `bin_folder/` | BIN logs downloaded from the STM32 |
| `wav_out/` | WAV output from option 8 |
| `teaching_data/` | Training WAV files per word (`kava/`, `pivo/`, `sok/`, `vino/`, `čaj/`) |
| `testing_data/` | 10 test WAV files per word (not used for training) |
| `signs_data/` | Sign-language videos per letter (`A.mov`, `Č.mov`, …) |
| `ai1.0.pkl` | Pre-trained audio model (words: kava, pivo, sok, vino, čaj) |

---

##  Project Goals

- Real-time sign language recognition  
- Speech-to-sign mapping (spoken word → letter videos)  
- Accessible communication tools  

---

##  Future Improvements

- Live audio input for option 11 (microphone or STM32 stream)  
- Expand sign video and training datasets  
- Improve model accuracy  
- Add real-time UI feedback  