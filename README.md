# toontown-corp-clash-client
This is a Python Botting/Hacked Client for Toontown Corporate Clash 1.4.5.

This project uses `win32api` ReadProcessMemory to fetch a Player's location and health, and then uses PyAutoGui to move the Player. Future releases will likely attempt to write to memory directly (allowing the bot to run in the background).

![image](https://github.com/hackerbuddy/toontown-corp-clash-client/assets/17036475/5f7717d4-d2c8-4be9-864e-b563d9ad8a15)

![corp-clash-bot](https://github.com/hackerbuddy/toontown-corp-clash-client/assets/17036475/86dc7de9-06b9-4121-abab-65aeea97f180)

### How to use
1. Clone repo, open directory
2. Open game, select character
3. `pip install -r requirements.txt` (or use a virtual environment https://docs.python.org/3/library/venv.html)
4. `python corp-clash-bot.py`

### Known limitations
Certain GUI interactions will cause our memory address to be freed (fishing menu will do this). If this happens, you will need to enter a building to load our memory values back into memory. Future releases will attempt to address this issue.

### Additional Exploits
CheatEngine Speed Hack is confirmed to work (DLL Injection). Use with caution -- expect to get banned!
