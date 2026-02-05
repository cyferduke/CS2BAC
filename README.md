![VAC Safe](https://img.shields.io/badge/VAC-Safe-brightgreen)
![Monkey Powered](https://img.shields.io/badge/Monkey-Powered-yellow)
# 🎧 CS2 Background Audio Controller
Based on [CS2MC](https://github.com/kittens/CS2MC) creds to [kittens](https://github.com/kittens)😼

## 🤔 What's this?
This app controls background audio volume while playing CS2, reacting to in‑game events such as dying, warm‑up, and more.  
It uses [Game State Integration](https://developer.valvesoftware.com/wiki/Counter-Strike:_Global_Offensive_Game_State_Integration), making it **VAC‑safe**.

## 🚀 How to use?

### 📋 Requirements
- Tested on **Windows 10/11**  
- Python **3.10 & 3.12** (⚠️ don't use 3.13 — `winsdk` currently broken there)  
- For packages see `requirements.txt`

### 🔧 Installation
Download master repo and extract somewhere.  
Open CMD or Terminal at destination and run:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
Move or copy gamestateintegrationcs2bac.cfg to CS2 cfg folder (for example:  
E:\Steam\SteamApps\common\Counter-Strike Global Offensive\game\csgo\cfg)

▶️ Usage
Launch main.py via venv you created by either typing in CMD/Terminal:
```bash
python main.py
```
or create a .bat file in main dir for daily usage:
```bat
@echo off
call venv\Scripts\activate
python main.py
```

Visit http://127.0.0.1:1337 in your web browser to configure and init.

🗑️ Uninstallation
- Remove gamestateintegrationcs2bac.cfg from CS2 cfg folder  
  (for example: E:\Steam\SteamApps\common\Counter-Strike Global Offensive\game\csgo\cfg)  
- Remove extracted files dir  
- (Optional) delete the venv folder if you created one

## 🪳 Bugs?
Did you encounter a bug?  
**Of course you did!** Thats cuz I'm a human-like monkey 🐒.  

If you find something broken, just laugh, and maybe open an issue.
But better don't do it or you will make me a sad monke 🥹.
