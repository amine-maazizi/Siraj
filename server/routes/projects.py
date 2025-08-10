# server/routes/projects.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from ..services.projects import (
    ProjectManifest, PROJECTS_ROOT, read_manifest, write_manifest,
    ensure_structure, set_active_paths, list_projects
)

router = APIRouter(prefix="/projects", tags=["projects"])

class SaveReq(BaseModel):
    title: str = Field(min_length=1)
    id: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_\-]+$")
    description: str | None = None
    brainrot_enabled: bool = False

class OpenReq(BaseModel):
    path: str

@router.get("", summary="List available .sirajproj files")
def get_projects():
    return {"projects": list_projects()}

@router.get("/current", summary="Read currently active project (if any)")
def get_current():
    from ..services.projects import get_active_paths
    active = get_active_paths()
    if not active:
        return {"active": None}
    mp = Path(active["manifest_path"])
    try:
        m = read_manifest(mp)
        return {"active": m, "paths": active}
    except Exception as e:
        raise HTTPException(400, f"Failed to read manifest: {e}")

@router.post("/save", summary="Create or update a project manifest and activate it")
def save_project(req: SaveReq):
    project_dir = PROJECTS_ROOT / req.id
    m = ProjectManifest.default(
        pid=req.id,
        title=req.title,
        description=req.description,
        brainrot_enabled=req.brainrot_enabled,
    )
    ensure_structure(project_dir, m)
    mp = write_manifest(project_dir, m)
    set_active_paths(project_dir, m)
    return {"ok": True, "manifest_path": str(mp.resolve()), "project": m}

@router.post("/open", summary="Open an existing .sirajproj and activate it")
def open_project(body: OpenReq):
    p = Path(body.path)
    if not p.exists() or p.suffix != ".sirajproj":
        raise HTTPException(400, "Invalid .sirajproj path")
    m = read_manifest(p)
    project_dir = p.parent
    ensure_structure(project_dir, m)
    set_active_paths(project_dir, m)
    return {"ok": True, "project": m}
