import sys
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(КОРІНЬ))
sys.path.insert(0, str(КОРІНЬ / "тести"))
