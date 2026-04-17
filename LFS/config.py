import os
from dotenv import load_dotenv
 
# Load .env file automatically
load_dotenv()
 
# ── AWS Credentials from .env ─────────────────────────────────────────────
AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME           = os.getenv("S3_BUCKET", "github-idc-storage")
REGION                = os.getenv("AWS_REGION", "ap-south-1")
 
# S3 folder structure:
# s3://testingknowledgebas/{project}/{file}
S3_BASE_PATH = "{project}"
 
# Local folder where metadata JSON files are saved
MANIFEST_DIR = "data-manifest"
 
# Supported file categories (auto-detected by extension)
FILE_CATEGORIES = {
    # Archives
    ".zip"  : "archives",
    ".tar"  : "archives",
    ".gz"   : "archives",
    ".rar"  : "archives",
    # Models
    ".pkl"  : "models",
    ".h5"   : "models",
    ".pt"   : "models",
    ".onnx" : "models",
    # Images
    ".png"  : "images",
    ".jpg"  : "images",
    ".jpeg" : "images",
    ".gif"  : "images",
    # Documents
    ".pdf"  : "docs",
    ".docx" : "docs",
    ".xlsx" : "docs",
    ".csv"  : "docs",
    # Code / Data
    ".json" : "data",
    ".xml"  : "data",
    ".sql"  : "data",
}
 
def get_category(filename):
    ext = os.path.splitext(filename)[1].lower()
    return FILE_CATEGORIES.get(ext, "misc")