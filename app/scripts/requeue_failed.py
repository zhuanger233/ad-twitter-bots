from app.db.repositories.subtitle_task_repo import SubtitleTaskRepository
from app.db.session import SessionLocal
from app.workers.tasks_pipeline import run_pipeline


if __name__ == "__main__":
    with SessionLocal() as session:
        repo = SubtitleTaskRepository(session)
        for task in repo.list_recent(limit=200):
            if task.status == "failed":
                run_pipeline.delay(str(task.id))
