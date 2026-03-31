# AISL
With the use of Artificial Intelligence, the goal of this project is to give it the capability to "read" sign language through video and make it show pictures of ASL gestures that the user said into their microphone.

#How to contribute

## 1. Clone repo to local machine
```bash
git clone https://github.com/teodorus12/AISL.git 
cd AI-OkroglaMiza
```

## 2. checkout to new branch
```bash
git checkout dev
git pull
```

## 3. Create new feature branch where you can implimente your own features
```bash
git checkout -b feature/ID-description
git push -u origin feature/ID-description
```

## 4. commit your changes
```bash
git add .
git commit -m "feature description"
git push
```
#How to connect

## 1. connect STM32 with USB micro and USB mini
both need to have data transfer

## 2. donwload putty (not needed but recomended)
### 2.1 link
-download link: https://putty.org/index.html

### 2.2 configure putty
-serial line COM5 (variable)
-speed 9600
-connection type: serial
-Under logging "all sesion output"
-Under terminal local echo "force on"

lastly save the sesion or you will need to do this every time

#How to test if connection works

##1. Open putty
##2. run "STREAM"
-if you see a stream of data it works
