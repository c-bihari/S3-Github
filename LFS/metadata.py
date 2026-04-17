# metadata.py - Handles metadata JSON generation and versioning

import json
import os
from datetime import datetime
from config import MANIFEST_DIR

def get_next_version(manifest_file):
    """Read existing manifest and increment version number."""
    if not os.path.exists(manifest_file):
        return "v1"
    try:
        with open(manifest_file) as f:
            data = json.load(f)
        version_num = int(data.get("version", "v1")[1:]) + 1
        return f"v{version_num}"
    except:
        return "v1"

def save_metadata(project, filename, s3_path, category):
    """Save upload metadata to a local JSON file."""
    os.makedirs(MANIFEST_DIR, exist_ok=True)

    name         = os.path.splitext(filename)[0]
    manifest_file = f"{MANIFEST_DIR}/{project}-{name}.json"
    version      = get_next_version(manifest_file)

    metadata = {
        "project"     : project,
        "filename"    : filename,
        "category"    : category,
        "s3_path"     : s3_path,
        "version"     : version,
        "uploaded_at" : datetime.now().isoformat(),
    }

    with open(manifest_file, "w") as f:
        json.dump(metadata, f, indent=2)

    return manifest_file, version

def load_metadata(project, filename):
    """Load existing metadata for a file."""
    name          = os.path.splitext(filename)[0]
    manifest_file = f"{MANIFEST_DIR}/{project}-{name}.json"

    if not os.path.exists(manifest_file):
        return None

    with open(manifest_file) as f:
        return json.load(f)
