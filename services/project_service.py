from sqlalchemy.orm import Session
from schemas.project_schema import ProjectOut
from models.project_model import Project
from schemas.project_schema import Milestone
from decimal import Decimal
from typing import List
from fastapi import  HTTPException
import json

def save_project(db: Session, user_id: int, data: dict, cost_usd: Decimal):
    project = Project(
        user_id=user_id,
        title=data["title"],
        description=data["description"],
        category=data["category"],
        tech_stack=data["tech_stack"],
        difficulty=data["difficulty"],
        milestones=data["milestones"], 
        cost_usd=cost_usd
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def get_projects_by_user(db: Session, user_id: int) -> list[ProjectOut]:
    projects = db.query(Project).filter(Project.user_id == user_id).all()

    for project in projects:
        if isinstance(project.milestones, str):  
            project.milestones = json.loads(project.milestones)

    return projects

def get_project_by_id(db: Session, project_id: int, user_id: int) -> ProjectOut:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if project and isinstance(project.milestones, str):
        project.milestones = json.loads(project.milestones)
    return project


def update_milestone_status_service(
    db: Session,
    user_id: int,
    project_id: int,
    milestone_number: int,
    is_completed: bool
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    milestones = json.loads(project.milestones) if isinstance(project.milestones, str) else project.milestones

    for milestone in milestones:
        if milestone["milestone_number"] == milestone_number:
            milestone["is_completed"] = is_completed
            for step in milestone.get("steps", []):
                step["is_done"] = is_completed
        elif milestone["milestone_number"] > milestone_number and not is_completed:
            milestone["is_completed"] = False
            for step in milestone.get("steps", []):
                step["is_done"] = False

    updated_fields = {
        "milestones": json.dumps(milestones) if isinstance(project.milestones, str) else milestones,
    }

    db.query(Project).filter(Project.id == project_id).update(updated_fields)
    db.commit()

    # Fetch and return updated project
    updated_project = db.query(Project).filter(Project.id == project_id).first()
    return updated_project


def update_step_status_service(
    db: Session,
    user_id: int,
    project_id: int,
    milestone_number: int,
    step_number: int,
    is_done: bool
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    milestones = json.loads(project.milestones) if isinstance(project.milestones, str) else project.milestones

    found = False
    for milestone in milestones:
        if milestone["milestone_number"] == milestone_number:
            for step in milestone["steps"]:
                if step["step_number"] == step_number:
                    step["is_done"] = is_done
                    found = True
                    break
            milestone["is_completed"] = all(s.get("is_done", False) for s in milestone["steps"])
            break

    if not found:
        raise HTTPException(status_code=404, detail="Step not found")

    project_done = all(m.get("is_completed", False) for m in milestones)

    updated_fields = {
        "milestones": json.dumps(milestones) if isinstance(project.milestones, str) else milestones,
        "is_project_done": project_done,
        "title": project.title,
    }

    db.query(Project).filter(Project.id == project_id).update(updated_fields)
    db.commit()

    updated_project = db.query(Project).filter(Project.id == project_id).first()
    return updated_project
