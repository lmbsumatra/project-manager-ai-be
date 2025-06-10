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

load_dotenv()

# request model
class ProjectRequest(BaseModel):
    prompt: str = Field(..., examples=["Create steps on how to make a blog system"])

# step item model
class StepItem(BaseModel):
    step_number: int
    description: str

# pesponse model
class ProjectResponse(BaseModel):
    project_name: str
    project_desc: str
    steps: list[StepItem]
    cost_usd: Decimal

# schema definitions for LangChain structured parser
schemas = [
    ResponseSchema(name="project_name", description="Name of the project"),
    ResponseSchema(name="project_desc", description="Description of the project"),
    ResponseSchema(name="steps", description="List of steps as JSON objects with 'step_number' and 'step_description' keys."),
]

# set up parser
parser = StructuredOutputParser.from_response_schemas(schemas)
format_instructions = parser.get_format_instructions()

# chat model
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# prompt template
prompt = PromptTemplate(
    template="""
You are an advanced AI project steps generator that outputs strictly structured JSON.

{user_prompt}

{format_instructions}
""",
    input_variables=["user_prompt"],
    partial_variables={"format_instructions": format_instructions},
)

# FastAPI setup
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# token counter
def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

# main endpoint
@app.post("/generate-steps", response_model=ProjectResponse)
async def generate_steps(req: ProjectRequest):
    try:
        formatted_prompt = prompt.format(user_prompt=req.prompt)
        response = await llm.ainvoke(formatted_prompt)
        parsed = parser.parse(response.content)

        # debug log
        logging.warning(f"Raw parsed steps: {parsed.get('steps')}")

        # validate and transform steps
        formatted_steps = []
        for i, step in enumerate(parsed.get("steps", [])):
            try:
                step_number = step.get("step_number") or i + 1
                description = step.get("description") or step.get("step_description") or ""
                if not description:
                    continue
                formatted_steps.append({
                    "step_number": int(step_number),
                    "description": description.strip()
                })
            except Exception as step_err:
                logging.error(f"Error parsing step {i}: {step_err}")
                continue

        # token count for cost estimation
        prompt_tokens = count_tokens(formatted_prompt)
        completion_tokens = count_tokens(response.content)
        cost = (
            Decimal(prompt_tokens) * Decimal("0.005") +
            Decimal(completion_tokens) * Decimal("0.015")
        ) / Decimal(1000)

        return {
            "project_name": parsed["project_name"],
            "project_desc": parsed["project_desc"],
            "steps": formatted_steps,
            "cost_usd": round(cost, 6)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
