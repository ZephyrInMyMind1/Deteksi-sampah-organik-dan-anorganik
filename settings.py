from pathlib import Path
import sys
from pathlib import Path
from sqlalchemy import create_engine

# Get the absolute path of the current file
FILE = Path(__file__).resolve()
# Get the parent directory of the current file
ROOT = FILE.parent
# Add the root path to the sys.path list if it is not already there
if ROOT not in sys.path:
    sys.path.append(str(ROOT))
# Get the relative path of the root directory with respect to the current working directory
ROOT = ROOT.relative_to(Path.cwd())

# Sources
IMAGE = 'Image'
WEBCAM = 'Webcam'

# Menghilangkan VIDEO dari sources list
SOURCES_LIST = [IMAGE, WEBCAM]

# Images config
IMAGES_DIR = ROOT / 'images'
DEFAULT_IMAGE = IMAGES_DIR / 'sebelumdeteksi.jpg'
DEFAULT_DETECT_IMAGE = IMAGES_DIR / 'hasildeteksi.jpg'

# ML Model config
MODEL_DIR = ROOT / 'weights'
DETECTION_MODEL = MODEL_DIR / 'best.pt'

# Webcam
WEBCAM_PATH = 0

# Database configuration
DATABASE_URL = "sqlite:///history.db"
engine = create_engine(DATABASE_URL)