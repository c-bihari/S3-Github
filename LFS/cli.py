# cli.py - Main CLI tool for uploading/downloading files to/from S3

import boto3
import click
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box
from rich.progress import (
    Progress, BarColumn, DownloadColumn,
    TransferSpeedColumn, TimeRemainingColumn, TextColumn
)
from config import BUCKET_NAME, REGION, S3_BASE_PATH, get_category
from metadata import save_metadata, load_metadata

console = Console()

# ── S3 client ────────────────────────────────────────────────────────────────
s3 = boto3.client("s3", region_name=REGION)


def get_s3_key(project, filename):
    """Build the full S3 key — project folder only, overwrites existing file."""
    category = get_category(filename)
    base     = S3_BASE_PATH.format(project=project)
    return f"{base}/{filename}", filename, category


def s3_error(e):
    """Return a friendly message for common S3 errors."""
    code = ""
    if hasattr(e, "response"):
        code = e.response.get("Error", {}).get("Code", "")
    if code == "NoSuchBucket":
        return f"Bucket '{BUCKET_NAME}' not found. Check S3_BUCKET in .env"
    if code in ("NoSuchKey", "404"):
        return "File not found in S3. Check project name and filename."
    if code in ("InvalidAccessKeyId", "SignatureDoesNotMatch", "AuthFailure"):
        return "Invalid AWS credentials. Run: setup.bat"
    if code == "AccessDenied":
        return "Access denied. Check your AWS permissions."
    return str(e)


def check_env():
    """Verify .env exists and credentials are set."""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_file):
        console.print("\n[red]❌ .env not found. Run: setup.bat[/red]\n")
        raise SystemExit(1)
    from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        console.print("\n[red]❌ AWS credentials missing in .env. Run: setup.bat[/red]\n")
        raise SystemExit(1)


# ── CLI GROUP ────────────────────────────────────────────────────────────────
@click.group()
@click.pass_context
def cli(ctx):
    """LFS -- Upload & download project files to/from S3."""
    if ctx.invoked_subcommand != "setup":
        check_env()


# ── UPLOAD ───────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("project")
@click.argument("file")
def upload(project, file):
    """Upload a file to S3 under the given project."""

    if not os.path.exists(file):
        console.print(f"\n[red]❌ File '{file}' not found![/red]\n")
        return

    s3_key, _, category = get_s3_key(project, file)
    s3_full_path = f"s3://{BUCKET_NAME}/{s3_key}"
    file_size    = os.path.getsize(file)
    file_size_mb = round(file_size / (1024 * 1024), 2)

    console.print(f"\n[yellow]Uploading '{file}'...[/yellow]")
    console.print(f"   Size     : {file_size_mb} MB")
    console.print(f"   Project  : {project}")
    console.print(f"   Category : {category}\n")

    try:
        with Progress(
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Uploading {file}", total=file_size)

            def on_progress(bytes_sent):
                progress.update(task, advance=bytes_sent)

            s3.upload_file(file, BUCKET_NAME, s3_key, Callback=on_progress)

        manifest_file, version = save_metadata(project, file, s3_full_path, category)

        console.print(f"\n[green]✅ Uploaded Successfully![/green]")

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
        console.print(f"\n[red]❌ Upload Failed: {s3_error(e)}[/red]\n")


# ── DOWNLOAD ─────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("project")
@click.argument("file")
def download(project, file):
    """Download the latest version of a file from S3 for the given project."""

    base   = S3_BASE_PATH.format(project=project)
    s3_key = f"{base}/{file}"

    # Warn before overwriting existing local file
    if os.path.exists(file):
        console.print(f"\n[yellow]⚠️  '{file}' already exists locally.[/yellow]")
        if not click.confirm("   Overwrite?", default=False):
            console.print("[cyan]Download cancelled.[/cyan]\n")
            return

    console.print(f"\n[yellow]Downloading latest '{file}'...[/yellow]")
    console.print(f"   Project  : {project}\n")

    try:
        # Get file size from S3 for progress bar
        head     = s3.head_object(Bucket=BUCKET_NAME, Key=s3_key)
        filesize = head["ContentLength"]

        with Progress(
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Downloading {file}", total=filesize)

            def on_progress(bytes_recv):
                progress.update(task, advance=bytes_recv)

            s3.download_file(BUCKET_NAME, s3_key, file, Callback=on_progress)

        file_size_mb = round(os.path.getsize(file) / (1024 * 1024), 2)
        metadata     = load_metadata(project, file)

        console.print(f"\n[green]✅ Downloaded Successfully![/green]")

        table = Table(box=box.ROUNDED, show_header=False, style="cyan")
        table.add_column("Key",   style="bold white", width=15)
        table.add_column("Value", style="white")
        table.add_row("Saved As",  file)
        table.add_row("Size",      f"{file_size_mb} MB")
        table.add_row("S3 Path",   f"s3://{BUCKET_NAME}/{s3_key}")
        if metadata:
            table.add_row("Version",   metadata.get("version", "unknown"))
            table.add_row("Uploaded",  metadata.get("uploaded_at", "unknown"))
        console.print(table)

    except Exception as e:
        console.print(f"\n[red]❌ Download Failed: {s3_error(e)}[/red]\n")


# ── DELETE ───────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("project")
@click.argument("file")
def delete(project, file):
    """Delete a file from S3 for the given project."""

    s3_key       = f"{S3_BASE_PATH.format(project=project)}/{file}"
    s3_full_path = f"s3://{BUCKET_NAME}/{s3_key}"

    console.print(f"\n[yellow]⚠️  You are about to delete:[/yellow]")
    console.print(f"   {s3_full_path}\n")

    if not click.confirm("   Confirm delete?", default=False):
        console.print("[cyan]Delete cancelled.[/cyan]\n")
        return

    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)

        # Remove local manifest if it exists
        from config import MANIFEST_DIR
        name          = os.path.splitext(file)[0]
        manifest_file = f"{MANIFEST_DIR}/{project}-{name}.json"
        if os.path.exists(manifest_file):
            os.remove(manifest_file)

        console.print(f"\n[green]✅ Deleted successfully![/green]")

        table = Table(box=box.ROUNDED, show_header=False, style="cyan")
        table.add_column("Key",   style="bold white", width=15)
        table.add_column("Value", style="white")
        table.add_row("Deleted",  file)
        table.add_row("Project",  project)
        table.add_row("S3 Path",  s3_full_path)
        table.add_row("At",       datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        console.print(table)

    except Exception as e:
        console.print(f"\n[red]❌ Delete Failed: {s3_error(e)}[/red]\n")


# ── LIST ─────────────────────────────────────────────────────────────────────
@cli.command(name="list")
@click.argument("project")
def list_files(project):
    """List all files in S3 for a given project."""

    console.print(f"\n[yellow]Listing files for project: {project}[/yellow]\n")

    try:
        prefix   = f"{project}/"
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
            category = get_category(name)
            size_mb  = round(obj["Size"] / (1024 * 1024), 2)
            modified = obj["LastModified"].strftime("%Y-%m-%d %H:%M")
            table.add_row(name, category, str(size_mb), modified)

        console.print(table)

    except Exception as e:
        console.print(f"\n[red]❌ List Failed: {s3_error(e)}[/red]\n")


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

    console.print(f"\n[yellow]Metadata for '{file}'[/yellow]\n")

    table = Table(box=box.ROUNDED, show_header=False, style="cyan")
    table.add_column("Key",   style="bold white", width=15)
    table.add_column("Value", style="white")

    for key, value in metadata.items():
        table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)


# ── SETUP ────────────────────────────────────────────────────────────────────
@cli.command()
def setup():
    """First-time setup -- create .env with your AWS credentials."""

    env_file = os.path.join(os.path.dirname(__file__), ".env")

    if os.path.exists(env_file):
        console.print("\n[yellow]⚠️  .env already exists.[/yellow]")
        overwrite = click.confirm("   Overwrite it?", default=False)
        if not overwrite:
            console.print("[cyan]Setup cancelled. Your existing .env was kept.[/cyan]\n")
            return

    console.print("\n[cyan]-- LFS Setup ---------------------------------[/cyan]")
    console.print("[white]Enter your AWS credentials (input is hidden):[/white]\n")

    access_key = click.prompt("  AWS Access Key ID",     hide_input=True)
    secret_key = click.prompt("  AWS Secret Access Key", hide_input=True)
    bucket     = click.prompt("  S3 Bucket",             default="testingknowledgebas")
    region     = click.prompt("  AWS Region",            default="us-east-1")

    with open(env_file, "w") as f:
        f.write("# AWS Credentials\n")
        f.write(f"AWS_ACCESS_KEY_ID={access_key}\n")
        f.write(f"AWS_SECRET_ACCESS_KEY={secret_key}\n\n")
        f.write("# S3 Config\n")
        f.write(f"S3_BUCKET={bucket}\n")
        f.write(f"AWS_REGION={region}\n")

    console.print("\n[green]✅ .env created successfully![/green]")

    console.print("\n[yellow]Testing AWS connection...[/yellow]")
    try:
        test_client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        test_client.head_bucket(Bucket=bucket)
        console.print(f"[green]✅ Connected to bucket '{bucket}' successfully![/green]\n")
    except Exception as e:
        console.print(f"[red]❌ Connection failed: {s3_error(e)}[/red]")
        console.print("[white]Check your credentials and bucket name in .env[/white]\n")


if __name__ == "__main__":
    cli()
