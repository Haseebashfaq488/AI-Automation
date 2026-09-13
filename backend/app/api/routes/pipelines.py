from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from app.modules.file_management.pipelines.organize_downloads_pipeline import OrganizeDownloadsPipeline
from app.modules.file_management.pipelines.organize_photos_pipeline import OrganizePhotosPipeline
from app.modules.file_management.pipelines.dedupe_folder_pipeline import DedupeFolderPipeline
from app.modules.file_management.pipelines.backup_documents_pipeline import BackupDocumentsPipeline
from app.modules.file_management.pipelines.archive_old_files_pipeline import ArchiveOldFilesPipeline
from app.modules.file_management.pipelines.sort_by_date_pipeline import SortByDatePipeline
from app.modules.whatsapp.pipelines.daily_digest_pipeline import DailyDigestPipeline
from app.modules.whatsapp.pipelines.downloads_notifier_pipeline import DownloadsNotifierPipeline
from app.modules.whatsapp.pipelines.photo_backup_pipeline import PhotoBackupPipeline
from app.modules.gmail.pipelines.list_recent_emails_pipeline import ListRecentEmailsPipeline

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

# Simple registry of pipelines
pipelines = {
    "organize_downloads": OrganizeDownloadsPipeline(),
    "organize_photos": OrganizePhotosPipeline(),
    "dedupe_folder": DedupeFolderPipeline(),
    "backup_documents": BackupDocumentsPipeline(),
    "archive_old_files": ArchiveOldFilesPipeline(),
    "sort_by_date": SortByDatePipeline(),
    "daily_digest": DailyDigestPipeline(),
    "downloads_notifier": DownloadsNotifierPipeline(),
    "photo_backup": PhotoBackupPipeline(),
    "list_recent_emails": ListRecentEmailsPipeline(),
}

@router.get("/list")
async def list_pipelines() -> Dict[str, Any]:
    """Return a list of available pipeline names."""
    return {"pipelines": list(pipelines.keys())}

@router.post("/run/{pipeline_name}")
async def run_pipeline(pipeline_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a pipeline by name with given parameters."""
    pipeline = pipelines.get(pipeline_name)
    if not pipeline:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found")
    try:
        return await pipeline.run(params)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
