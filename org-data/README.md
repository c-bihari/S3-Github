# org-data CLI Tool

Upload and download project files to/from AWS S3 with automatic versioning and metadata tracking.

---

## Setup (One Time)

### 1. Install Python dependencies
```cmd
pip install -r requirements.txt
```

### 2. AWS credentials (already configured via AWS CLI)
```cmd
aws configure
```

### 3. Add to PATH (so you can run from anywhere)
- Copy the `org-data` folder to `C:\tools\org-data\`
- Add `C:\tools\org-data\` to your system PATH
- Now run `org-data` from any folder!

---

## Commands

### Upload a file
```cmd
org-data upload <project> <file>
```
Example:
```cmd
org-data upload project-a model-v1.pkl
org-data upload project-a data.zip
org-data upload project-a report.pdf
```

### Download a file
```cmd
org-data download <project> <file>
```
Example:
```cmd
org-data download project-a model-v1-2026-04-16.pkl
```

### List all files for a project
```cmd
org-data list <project>
```
Example:
```cmd
org-data list project-a
```

### Show file metadata
```cmd
org-data info <project> <file>
```
Example:
```cmd
org-data info project-a model-v1.pkl
```

---

## S3 Folder Structure

```
s3://testingknowledgebas/
└── project-a/
    └── prod/
        ├── archives/    ← .zip, .tar, .gz
        ├── models/      ← .pkl, .h5, .pt
        ├── images/      ← .png, .jpg
        ├── docs/        ← .pdf, .docx, .xlsx
        ├── data/        ← .json, .csv, .xml
        └── misc/        ← everything else
```

---

## Auto Versioning

Every upload adds a date stamp automatically:
```
model-v1.pkl  →  model-v1-2026-04-16.pkl
data.zip      →  data-2026-04-16.zip
```

---

## Metadata

Every upload creates a JSON file in `data-manifest/`:
```json
{
  "project": "project-a",
  "filename": "model-v1.pkl",
  "category": "models",
  "s3_path": "s3://testingknowledgebas/project-a/prod/models/model-v1-2026-04-16.pkl",
  "version": "v1",
  "uploaded_at": "2026-04-16T10:30:00"
}
```
