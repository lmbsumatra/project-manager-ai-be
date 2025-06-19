from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.project_schema import ProjectCreate, ProjectOut, ProjectGenerated
from services.project_service import save_project, get_projects_by_user, get_project_by_id, update_milestone_status_service, update_step_status_service
from db.database import get_db
from utils.langchain_engine import generate_project_data
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
from schemas.project_schema import UpdateMilestoneStatus, UpdateStepStatus, ProjectOut
from services.project_service import update_milestone_status_service, update_step_status_service


load_dotenv()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, "your_super_secret_key", algorithms="HS256")
        sub = payload.get("sub")
        user_id = int(sub)  
        return user_id
    except (JWTError, ValueError, TypeError) as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/generate", response_model=ProjectGenerated)
async def generate_project(
    req: ProjectCreate,
    user_id: int = Depends(get_current_user_id)
):
    data, cost = await generate_project_data(req.prompt)
    return {"data": data, "cost": cost}

@router.post("/save", response_model=ProjectOut)
def save_generated_project(
    project: ProjectGenerated,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    saved = save_project(db, user_id, project.data, project.cost)
    return saved
 

@router.get("/", response_model=list[ProjectOut])
def list_user_projects(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_projects_by_user(db, user_id)

@router.get("/{project_id}", response_model=ProjectOut)
def get_single_project(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    project = get_project_by_id(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectGenerated

@router.patch("/{project_id}/milestone", response_model=ProjectOut)
def update_milestone_status(
    project_id: int,
    update: UpdateMilestoneStatus,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    try:
        result = update_milestone_status_service(db, user_id, project_id, update.milestone_number, update.is_completed)
        if result is None:
            raise HTTPException(status_code=500, detail="Service returned None")
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in update_milestone_status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{project_id}/milestone/step", response_model=ProjectOut)
def update_step_status(
    project_id: int,
    update: UpdateStepStatus,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    try:
        # print(f"Input params: user_id={user_id}, project_id={project_id}, milestone_number={update.milestone_number}, step_number={update.step_number}, is_done={update.is_done}")
        
        result = update_step_status_service(db, user_id, project_id, update.milestone_number, update.step_number, update.is_done)
        
        print(f"Service returned: {result}")
        print(f"Result type: {type(result)}")
        
        if result is None:
            raise HTTPException(status_code=500, detail="Service returned None")
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in update_step_status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")