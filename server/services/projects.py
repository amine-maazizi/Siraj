# server/services/projects.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import time

PROJECTS_ROOT = Path("SirajProjects")
ACTIVE_PATHS_FILE = Path("server/store/active_paths.json")

@dataclass
class ProjectManifest:
    version: int
    id: str                  # slug/safe id
    title: str
    description: str | None
    brainrot_enabled: bool
    created_at: float
    updated_at: float
    # relative to project_dir
    sqlite_path: str         # "sqlite.db"
    chroma_dir: str          # "chroma"
    media_dir: str           # "media"
    resources_dir: str       # "resources"
    # optional convenience fields
    last_doc_id: str | None = None

    @staticmethod
    def default(pid: str, title: str, description: str | None = None, brainrot_enabled=False):
        now = time.time()
        return ProjectManifest(
            version=1,
            id=pid,
            title=title,
            description=description,
            brainrot_enabled=brainrot_enabled,
            created_at=now,
            updated_at=now,
            sqlite_path="sqlite.db",
            chroma_dir="chroma",
            media_dir="media",
            resources_dir="resources",
            last_doc_id=None,
        )

def project_dir_from_path(path: Path) -> Path:
    # if a .sirajproj file path is passed, its parent folder is the project dir
    if path.suffix == ".sirajproj":
        return path.parent
    return path

def manifest_path(project_dir: Path) -> Path:
    # store manifest alongside the project folder, named <id>.sirajproj
    return project_dir.with_suffix(".sirajproj") if project_dir.suffix == "" else project_dir

def read_manifest(path: Path) -> ProjectManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ProjectManifest(**data)

def write_manifest(project_dir: Path, manifest: ProjectManifest) -> Path:
    p = manifest_path(project_dir / manifest.id).with_suffix(".sirajproj")
    p.parent.mkdir(parents=True, exist_ok=True)
    manifest.updated_at = time.time()
    p.write_text(json.dumps(asdict(manifest), indent=2), encoding="utf-8")
    return p

def ensure_structure(project_dir: Path, manifest: ProjectManifest):
    (project_dir / manifest.resources_dir).mkdir(parents=True, exist_ok=True)
    (project_dir / manifest.media_dir).mkdir(parents=True, exist_ok=True)
    (project_dir / manifest.chroma_dir).mkdir(parents=True, exist_ok=True)
    # sqlite file is created on first use by SQLAlchemy/SQLite if not exists

def set_active_paths(project_dir: Path, manifest: ProjectManifest):
    ACTIVE_PATHS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "sqlite_path": str((project_dir / manifest.sqlite_path).resolve()),
        "chroma_dir": str((project_dir / manifest.chroma_dir).resolve()),
        "media_dir":  str((project_dir / manifest.media_dir).resolve()),
        "project_id": manifest.id,
        "project_title": manifest.title,
        "manifest_path": str((manifest_path(project_dir / manifest.id)).resolve()),
    }
    ACTIVE_PATHS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def get_active_paths() -> dict | None:
    if not ACTIVE_PATHS_FILE.exists():
        return None
    return json.loads(ACTIVE_PATHS_FILE.read_text(encoding="utf-8"))

def list_projects() -> list[dict]:
    # scan SirajProjects/*/*.sirajproj
    items = []
    if not PROJECTS_ROOT.exists():
        return items
    for p in PROJECTS_ROOT.glob("**/*.sirajproj"):
        try:
            m = read_manifest(p)
            items.append({
                "title": m.title,
                "id": m.id,
                "path": str(p.resolve()),
                "updated_at": m.updated_at,
            })
        except Exception:
            continue
    # newest first
    items.sort(key=lambda x: x["updated_at"], reverse=True)
    return items
