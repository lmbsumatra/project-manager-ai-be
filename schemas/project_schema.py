from pydantic import BaseModel
from typing import List
from decimal import Decimal

class ProjectGenerated(BaseModel):
    data: dict
    cost: float

class StepItem(BaseModel):
    step_number: int
    description: str
    is_done: bool = False

class Milestone(BaseModel):
    milestone_number: int
    title: str
    steps: List[StepItem]
    is_completed: bool = False

class ProjectCreate(BaseModel):
    prompt: str

class ProjectOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    tech_stack: List[str]
    difficulty: str
    milestones: List[Milestone]
    cost_usd: Decimal
    is_project_done: bool = False

model_config = {
    "from_attributes": True
}

class UpdateMilestoneStatus(BaseModel):
    milestone_number: int
    is_completed: bool

class UpdateStepStatus(BaseModel):
    milestone_number: int
    step_number: int
    is_done: bool
