from sqlalchemy.orm import Session
from .models import Task, ExecutionLog
from typing import Optional, List

class Repository:
    def __init__(self, db_session: Session):
        self.db = db_session

    # Task operations
    def create_task(self, name: str, status: str = "pending") -> Task:
        task = Task(name=name, status=status)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def update_task_status(self, task_id: int, status: str) -> Optional[Task]:
        task = self.get_task(task_id)
        if task:
            task.status = status
            self.db.commit()
            self.db.refresh(task)
        return task

    def list_tasks(self) -> List[Task]:
        return self.db.query(Task).all()

    # ExecutionLog operations
    def log_execution(
        self,
        tool_name: str,
        input_data: Optional[str] = None,
        output_data: Optional[str] = None,
        success: bool = True,
        task_id: Optional[int] = None,
    ) -> ExecutionLog:
        log = ExecutionLog(
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            success=1 if success else 0,
            task_id=task_id,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
