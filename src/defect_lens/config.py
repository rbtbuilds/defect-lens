from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root: Path
    model_dir: Path | None = None
    max_image_bytes: int = 8 * 1024 * 1024
    max_body_bytes: int = 9 * 1024 * 1024
    max_pixels: int = 8_000_000
    max_pending: int = 32
    max_storage_bytes: int = 512 * 1024 * 1024
    max_jobs: int = 10_000
    job_timeout: float = 30.0
    worker_memory_mb: int = 1536
    lease_path: Path = Path("/tmp/bentolabs-portfolio-ml.lock")

    @property
    def runtime(self) -> Path:
        return self.root.resolve() / ".runtime"

    @property
    def database_path(self) -> Path:
        return self.runtime / "defect-lens.sqlite3"
