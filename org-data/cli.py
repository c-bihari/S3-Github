# cli.py - Main CLI tool for uploading/downloading files to/from S3

import boto3
import click
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box
from config import BUCKET_NAME, REGION, S3_BASE_PATH, get_category
from metadata import save_metadata, load_metadata

console = Console()

# ── S3 client (uses AWS CLI credentials automatically) ──────────────────────
s3 = boto3.client("s3", region_name=REGION)

def get_s3_key(project, filename):
    """Build the full S3 key with auto category + date versioning."""
    date     = datetime.now().strftime("%Y-%m-%d")
    name, ext = os.path.splitext(filename)
    category = get_category(filename)
    base     = S3_BASE_PATH.format(project=project, category=category)
    versioned = f"{name}-{date}{ext}"
    return f"{base}/{versioned}", versioned, category


# ── CLI GROUP ────────────────────────────────────────────────────────────────
@click.group()
def cli():
    """org-data — Upload & download project files to/from S3."""
    pass


# ── UPLOAD ───────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("project")
@click.argument("file")
def upload(project, file):
    """Upload a file to S3 under the given project."""

    if not os.path.exists(file):
        console.print(f"\n[red]❌ ERROR: File '{file}' not found![/red]\n")
        return

    s3_key, versioned_name, category = get_s3_key(project, file)
    s3_full_path = f"s3://{BUCKET_NAME}/{s3_key}"
    file_size    = os.path.getsize(file)
    file_size_mb = round(file_size / (1024 * 1024), 2)

    console.print(f"\n[yellow]📤 Uploading '{file}' to S3...[/yellow]")
    console.print(f"   Size     : {file_size_mb} MB")
    console.print(f"   Project  : {project}")
    console.print(f"   Category : {category}")

    try:
        s3.upload_file(file, BUCKET_NAME, s3_key)
        manifest_file, version = save_metadata(project, file, s3_full_path, category)

        console.print(f"\n[green]✅ Uploaded Successfully![/green]")

        # Pretty output table
        table = Table(box=box.ROUNDED, show_header=False, style="cyan")
        table.add_column("Key",   style="bold white", width=15)
        table.add_column("Value", style="white")
        table.add_row("S3 Path",   s3_full_path)
        table.add_row("Version",   version)
        table.add_row("Category",  category)
        table.add_row("Metadata",  manifest_file)
        table.add_row("Uploaded",  datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        console.print(table)

    except Exception as e:
        console.print(f"\n[red]❌ Upload Failed: {str(e)}[/red]\n")


# ── DOWNLOAD ─────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("project")
@click.argument("file")
def download(project, file):
    """Download a file from S3 for the given project."""

    category = get_category(file)
    base     = S3_BASE_PATH.format(project=project, category=category)
    s3_key   = f"{base}/{file}"

    console.print(f"\n[yellow]📥 Downloading '{file}' from S3...[/yellow]")
    console.print(f"   Project  : {project}")
    console.print(f"   Category : {category}")

    try:
        s3.download_file(BUCKET_NAME, s3_key, file)

        file_size    = os.path.getsize(file)
        file_size_mb = round(file_size / (1024 * 1024), 2)

        console.print(f"\n[green]✅ Downloaded Successfully![/green]")

        table = Table(box=box.ROUNDED, show_header=False, style="cyan")
        table.add_column("Key",   style="bold white", width=15)
        table.add_column("Value", style="white")
        table.add_row("Saved As",  file)
        table.add_row("Size",      f"{file_size_mb} MB")
        table.add_row("S3 Path",   f"s3://{BUCKET_NAME}/{s3_key}")
        console.print(table)

    except Exception as e:
        console.print(f"\n[red]❌ Download Failed: {str(e)}[/red]\n")


# ── LIST ─────────────────────────────────────────────────────────────────────
@cli.command(name="list")
@click.argument("project")
def list_files(project):
    """List all files in S3 for a given project."""

    console.print(f"\n[yellow]📋 Listing files for project: {project}[/yellow]\n")

    try:
        prefix   = f"{project}/prod/"
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)

        if "Contents" not in response:
            console.print(f"[red]No files found for project '{project}'[/red]\n")
            return

        table = Table(box=box.ROUNDED, style="cyan")
        table.add_column("File",          style="bold white")
        table.add_column("Category",      style="yellow")
        table.add_column("Size (MB)",     style="green")
        table.add_column("Last Modified", style="white")

        for obj in response["Contents"]:
            key      = obj["Key"]
            name     = key.split("/")[-1]
            category = key.split("/")[2] if len(key.split("/")) > 2 else "misc"
            size_mb  = round(obj["Size"] / (1024 * 1024), 2)
            modified = obj["LastModified"].strftime("%Y-%m-%d %H:%M")
            table.add_row(name, category, str(size_mb), modified)

        console.print(table)

    except Exception as e:
        console.print(f"\n[red]❌ List Failed: {str(e)}[/red]\n")


# ── INFO ──────────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("project")
@click.argument("file")
def info(project, file):
    """Show metadata info for an uploaded file."""

    metadata = load_metadata(project, file)

    if not metadata:
        console.print(f"\n[red]No metadata found for '{file}' in project '{project}'[/red]\n")
        return

    console.print(f"\n[yellow]📄 Metadata for '{file}'[/yellow]\n")

    table = Table(box=box.ROUNDED, show_header=False, style="cyan")
    table.add_column("Key",   style="bold white", width=15)
    table.add_column("Value", style="white")

    for key, value in metadata.items():
        table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)


if __name__ == "__main__":
    cli()
