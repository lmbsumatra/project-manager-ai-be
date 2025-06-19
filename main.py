from fastapi import FastAPI
from db.database import engine
from db.base import Base
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_routes 
from routes import project_routes 

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(project_routes.router, prefix="/projects", tags=["projects"])
