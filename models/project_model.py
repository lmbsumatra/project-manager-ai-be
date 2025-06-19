from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Numeric, Boolean
from db.base import Base
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import JSON

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(String)
    category = Column(String)
    tech_stack = Column(JSON)
    difficulty = Column(String)

   
    milestones = Column(MutableList.as_mutable(JSON), nullable=False)


    cost_usd = Column(Numeric)
    is_project_done = Column(Boolean, default=False)
