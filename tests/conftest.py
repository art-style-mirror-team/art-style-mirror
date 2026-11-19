import sys
from pathlib import Path

# 저장소 루트를 import 경로에 넣어 `import app`, `from modules import ...`가 되게 한다.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
