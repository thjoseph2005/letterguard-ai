"""Local file ingestion helpers for LetterGuard AI."""

from pathlib import Path
from shutil import copyfileobj


def create_directory_if_not_exists(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def validate_file_type(filename: str, allowed_extensions: list[str]) -> bool:
    if "." not in filename:
        return False
    extension = f".{filename.rsplit('.', 1)[-1].lower()}"
    allowed = {ext.lower() for ext in allowed_extensions}
    return extension in allowed


def save_uploaded_file(upload_file, target_dir: str) -> str:
    safe_name = Path(upload_file.filename).name
    create_directory_if_not_exists(target_dir)

    destination = Path(target_dir) / safe_name
    with destination.open("wb") as buffer:
        copyfileobj(upload_file.file, buffer)

    return str(destination)
