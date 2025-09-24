# B2-check-bucket-size-tool

# Check Bucket Size Tool (Backblaze B2, S3-compatible)

A tiny Tkinter + boto3 GUI that calculates **bucket size** for Backblaze B2:
- **Billable size (all versions)** — sums S3 `ListObjectVersions` (matches dashboard billing)
- **Current size (latest only)** — sums S3 `ListObjectsV2`

> Uses Backblaze’s S3-compatible endpoint (e.g (default)., `https://s3.us-west-004.backblazeb2.com`).

## Features
- Key ID / Application Key / Region / (optional) Bucket name
- Progress bar + live running total
- Human-readable output

## Prerequisites
- Python 3.9+
- `pip install -r requirements.txt`
- Backblaze **Key ID** + **Application Key**
- Region (e.g. `us-west-004`, `eu-central-003`, `us-east-005`)

## Run
python src/b2_bucket_size_gui.py
