import sys
from pathlib import Path

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # PyInstaller
    BASE = Path(sys._MEIPASS) / 'runekit'
else:
    BASE = Path(__file__).parent
