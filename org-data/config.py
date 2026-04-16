# config.py - All settings for org-data CLI tool

BUCKET_NAME = "testingknowledgebas"
REGION      = "us-east-1"

# S3 folder structure:
# s3://testingknowledgebas/{project}/prod/{category}/{file}
S3_BASE_PATH = "{project}/prod/{category}"

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
    import os
    ext = os.path.splitext(filename)[1].lower()
    return FILE_CATEGORIES.get(ext, "misc")
