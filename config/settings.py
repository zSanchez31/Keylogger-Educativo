from pathlib import Path
import platform

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "keystrokes.enc"
KEY_FILE = BASE_DIR / "config" / ".key"
MAX_LOG_SIZE = 10 * 1024 * 1024
LOG_ROTATION = True
CLEANUP_DAYS = 30
SYSTEM = platform.system().lower()
IS_WINDOWS = SYSTEM == "windows"
IS_LINUX = SYSTEM == "linux"
IS_MACOS = SYSTEM == "darwin"
APP_NAME = "keylogger_educativo_seguro"
APP_VERSION = "1.2.0"
DEFAULT_READ_LIMIT = 20
MAX_EXPORT_ROWS = 50000
LOG_DIR.mkdir(parents=True, exist_ok=True)
