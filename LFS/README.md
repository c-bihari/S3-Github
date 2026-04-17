# LFS CLI Tool

Upload and download project files to/from AWS S3 with automatic versioning and metadata tracking.

---

## Developer Setup (One Time)

### Step 1 — Clone the repo
```cmd
git clone https://github.com/Dyad-Inc/PUMAA.git
cd PUMAA\LFS
```

### Step 2 — Run setup
```cmd
setup.bat
```
This will automatically:
- Install all Python dependencies
- Ask for your AWS credentials (input is hidden)
- Create your `.env` file
- Test the S3 connection

> `.env` is git-ignored — AWS keys are never committed.

---

## Commands

### Upload a file
```cmd
LFS upload <project-name> <file-name>
```
```cmd
LFS upload PUMAA node_module.zip
```

### Download a file (always latest)
```cmd
LFS download <project-name> <file-name>
```
```cmd
LFS download PUMAA node_module.zip
```

### List all files for a project
```cmd
LFS list PUMAA
```

### Show file metadata / version
```cmd
LFS info PUMAA node_module.zip
```

---

## Project Files

| File | Purpose |
|---|---|
| `requirements.txt` | All Python packages |
| `.env.example` | Template — reference for what goes in `.env` |
| `.env` | Git-ignored — each dev has their own with real credentials |
| `setup.bat` | One-time setup — run after cloning |
| `LFS.bat` | Shortcut to run CLI commands |

---

## S3 Folder Structure

```
s3://testingknowledgebas/
└── {project}/
    └── {file}        ← upload overwrites, always latest
```

---

## Metadata (auto-saved locally)

Every upload saves a JSON file in `data-manifest/`:
```json
{
  "project": "PUMAA",
  "filename": "node_module.zip",
  "category": "archives",
  "s3_path": "s3://testingknowledgebas/PUMAA/node_module.zip",
  "version": "v2",
  "uploaded_at": "2026-04-17T10:22:49"
}
```
