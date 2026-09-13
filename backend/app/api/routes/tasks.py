from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.modules.database.db import SessionLocal
from app.modules.database.repository import Repository

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/list")
async def list_tasks(db: Session = Depends(get_db)) -> Dict[str, Any]:
    repo = Repository(db)
    tasks = repo.list_tasks()
    return {"tasks": [
        {"id": t.id, "name": t.name, "status": t.status, "created_at": t.created_at.isoformat(), "updated_at": t.updated_at.isoformat()}
        for t in tasks
    ]}

@router.post("/create")
async def create_task(payload: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="'name' field required")
    repo = Repository(db)
    task = repo.create_task(name=name)
    return {"id": task.id, "name": task.name, "status": task.status}

@router.get("/{task_id}")
async def get_task(task_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    repo = Repository(db)
    task = repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"id": task.id, "name": task.name, "status": task.status, "created_at": task.created_at.isoformat(), "updated_at": task.updated_at.isoformat()}

@router.patch("/{task_id}")
async def update_task_status(task_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    status = payload.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="'status' field required")
    repo = Repository(db)
    task = repo.update_task_status(task_id, status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"id": task.id, "name": task.name, "status": task.status}
