from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy import create_engine, Column, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from databases import Database

DATABASE_URL = "mysql+mysqlconnector://user_ababilw:ababil312@db4free.net:3306/ababil_dbw"
database = Database(DATABASE_URL)
Base = declarative_base()

# Model Database
class ProjectDB(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))  # Specify length for UUID
    name = Column(String(255))  # Example length, adjust based on your needs
    description = Column(String(255), nullable=True)  # Example length, adjust based on your needs

class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))  # Specify length for UUID
    project_id = Column(String(36), ForeignKey('projects.id'))  # Specify length for UUID
    name = Column(String(255))  # Example length, adjust based on your needs
    description = Column(String(255), nullable=True)  # Example length, adjust based on your needs
    completed = Column(Boolean, default=False)
    project = relationship("ProjectDB", back_populates="tasks")

ProjectDB.tasks = relationship("TaskDB", order_by=TaskDB.id, back_populates="project")

# SQLAlchemy session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for request and response
class Project(BaseModel):
    id: Optional[UUID] = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None

class Task(BaseModel):
    id: Optional[UUID] = Field(default_factory=uuid4)
    project_id: UUID
    name: str
    description: Optional[str] = None
    completed: bool = False

# CRUD operations for Project (similar to previous example)
# Add CRUD operations for Task here

@app.post("/tasks/", response_model=Task)
async def create_task(task: Task):
    query = TaskDB.__table__.insert().values(id=task.id, project_id=task.project_id, name=task.name, description=task.description, completed=task.completed)
    last_record_id = await database.execute(query)
    return {**task.dict(), "id": last_record_id}

@app.get("/tasks/", response_model=List[Task])
async def get_tasks():
    query = TaskDB.__table__.select()
    return await database.fetch_all(query)

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: UUID, task: Task):
    query = TaskDB.__table__.update().where(TaskDB.id == str(task_id)).values(name=task.name, description=task.description, completed=task.completed)
    await database.execute(query)
    return {**task.dict(), "id": task_id}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: UUID):
    query = TaskDB.__table__.delete().where(TaskDB.id == str(task_id))
    await database.execute(query)
    return {"message": "Task deleted"}