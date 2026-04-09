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

##  Project Goals

- Real-time sign language recognition  
- Speech-to-ASL visual mapping  
- Accessible communication tools  

---

##  Future Improvements

- Expand ASL dataset  
- Improve model accuracy  
- Add real-time UI feedback  
- Cross-platform support  