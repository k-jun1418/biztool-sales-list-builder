from pathlib import Path
from datetime import datetime


def write_error_log(message: str):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "error.log"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"[{now}] {message}\n")