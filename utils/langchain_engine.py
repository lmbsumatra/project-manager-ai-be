from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import os
import tiktoken
from decimal import Decimal

# Define schemas
schemas = [
    ResponseSchema(name="title", description="Name of the project"),
    ResponseSchema(name="description", description="Short summary"),
    ResponseSchema(name="category", description="Project category"),
    ResponseSchema(name="tech_stack", description="List of technologies"),
    ResponseSchema(name="difficulty", description="Difficulty"),
    ResponseSchema(
    name="milestones",
    description=(
        "A list of milestones, each with a `title` and an array of `steps`. "
        "Each step must have a `description` field. "
        "Titles must describe what the milestone is about (e.g. 'Setup Project Environment', 'Build UI Components')"
    )
)
]
parser = StructuredOutputParser.from_response_schemas(schemas)
format_instructions = parser.get_format_instructions()

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

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

async def generate_project_data(user_prompt: str):
    formatted_prompt = prompt.format(user_prompt=user_prompt)
    response = await llm.ainvoke(formatted_prompt)
    parsed = parser.parse(response.content)

    milestones = []
    for i, m in enumerate(parsed["milestones"]):
        title = m.get("milestone_title") or m.get("title") or f"Milestone {i}"
        steps = []
        for j, s in enumerate(m["steps"]):
            if isinstance(s, dict):
                desc = s.get("description", "")
            else:
                desc = str(s).strip()

            if desc:
                steps.append({
                    "step_number": j,
                    "description": desc,
                    "is_done": False, 
                })

        milestones.append({
            "milestone_number": i,
            "title": title,
            "steps": steps,
            "is_completed": False,  
        })

    tech_stack = parsed["tech_stack"]
    if isinstance(tech_stack, str):
        tech_stack = [x.strip() for x in tech_stack.split(",")]

    prompt_tokens = count_tokens(formatted_prompt)
    completion_tokens = count_tokens(response.content)
    cost = (Decimal(prompt_tokens) * Decimal("0.005") + Decimal(completion_tokens) * Decimal("0.015")) / Decimal(1000)

    return {
        "title": parsed["title"],
        "description": parsed["description"],
        "category": parsed["category"],
        "tech_stack": tech_stack,
        "difficulty": parsed["difficulty"],
        "milestones": milestones,
        "is_project_done": False  
    }, round(cost, 6)
