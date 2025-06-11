from decimal import Decimal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import tiktoken
from fastapi.middleware.cors import CORSMiddleware
import logging

# Load environment variables
load_dotenv()

# -------------------------------
# Pydantic Models
# -------------------------------

class ProjectRequest(BaseModel):
    prompt: str = Field(..., examples=["Create steps on how to make a blog system using Next.js and Tailwind CSS."])

class StepItem(BaseModel):
    step_number: int
    description: str

class Milestone(BaseModel):
    milestone_number: int
    title: str
    steps: list[StepItem]

class ProjectResponse(BaseModel):
    title: str
    description: str
    category: str
    tech_stack: list[str]
    difficulty: str
    milestones: list[Milestone]
    cost_usd: Decimal

# -------------------------------
# LangChain Response Schema
# -------------------------------

schemas = [
    ResponseSchema(name="title", description="Name of the project"),
    ResponseSchema(name="description", description="Short summary of the project"),
    ResponseSchema(name="category", description="Category of the project, such as 'Web Development', 'Game', 'Data Science'"),
    ResponseSchema(name="tech_stack", description="List of technologies used in the project, such as 'React', 'Next.js', 'Tailwind CSS'"),
    ResponseSchema(name="difficulty", description="Difficulty level of the project, either 'Beginner', 'Intermediate', or 'Advanced'"),
    ResponseSchema(name="milestones", description="""
List of milestones, each with a 'milestone_title' and a 'steps' list.
Each step is an object with 'step_number' and 'description' keys.
"""),
]

parser = StructuredOutputParser.from_response_schemas(schemas)
format_instructions = parser.get_format_instructions()

# -------------------------------
# LLM and Prompt Setup
# -------------------------------

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt = PromptTemplate(
    template="""
You are an expert AI assistant for beginner developers. Given a project prompt, return a clearly structured JSON with project metadata, milestones, and granular steps.

{user_prompt}

{format_instructions}

Respond only in valid JSON.
""",
    input_variables=["user_prompt"],
    partial_variables={"format_instructions": format_instructions},
)

# -------------------------------
# FastAPI Setup
# -------------------------------

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Token Counting for Cost Estimation
# -------------------------------

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

# -------------------------------
# Main Endpoint
# -------------------------------

@app.post("/generate-steps", response_model=ProjectResponse)
async def generate_steps(req: ProjectRequest):
    try:
        formatted_prompt = prompt.format(user_prompt=req.prompt)
        response = await llm.ainvoke(formatted_prompt)
        parsed = parser.parse(response.content)

               # Validate and transform milestones with milestone_number
        validated_milestones = []
        for idx, milestone in enumerate(parsed.get("milestones", []), start=1):
            milestone_title = milestone.get("milestone_title") or milestone.get("title") or f"Milestone {idx}"
            steps = []
            for i, step in enumerate(milestone.get("steps", [])):
                try:
                    step_number = step.get("step_number") or i + 1
                    description = step.get("description") or step.get("step_description") or ""
                    if not description:
                        continue
                    steps.append(StepItem(
                        step_number=int(step_number),
                        description=description.strip()
                    ))
                except Exception as step_err:
                    logging.error(f"Error parsing step {i} in milestone '{milestone_title}': {step_err}")
            if steps:
                validated_milestones.append(Milestone(
                    milestone_number=idx,
                    title=milestone_title.strip(),
                    steps=steps
                ))

        # Token-based cost estimation
        prompt_tokens = count_tokens(formatted_prompt)
        completion_tokens = count_tokens(response.content)
        cost = (
            Decimal(prompt_tokens) * Decimal("0.005") +
            Decimal(completion_tokens) * Decimal("0.015")
        ) / Decimal(1000)

       # Ensure tech_stack is a proper list
        tech_stack = parsed.get("tech_stack")
        if isinstance(tech_stack, str):
            tech_stack = [t.strip() for t in tech_stack.split(",")]
        elif not isinstance(tech_stack, list):
            tech_stack = []

        return {
            "title": parsed["title"],
            "description": parsed["description"],
            "category": parsed["category"],
            "tech_stack": tech_stack,
            "difficulty": parsed["difficulty"],
            "milestones": validated_milestones,
            "cost_usd": round(cost, 6)
        }


    except Exception as e:
        logging.exception("Error generating steps")
        raise HTTPException(status_code=500, detail=str(e))
