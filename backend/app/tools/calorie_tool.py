from langchain.tools import StructuredTool
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment.")

class CalorieInput(BaseModel):
    food: str

llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=openai_api_key)

def estimate_calorie(food: str) -> str:
    prompt = f"""
You are a nutrition assistant. Estimate the nutrition values for the given food item using standard nutritional knowledge.

For: "{food}"
Provide values **per 100g** or **1 standard serving**, whichever makes more sense.

Respond in this format (no extra commentary):
Calories: <value>
Protein: <value>g
Carbs: <value>g
Fat: <value>g

Examples:
Calories: 155
Protein: 13g
Carbs: 0g
Fat: 11g

Now estimate for:
{food}
""".strip()

    response = llm.invoke(prompt).content.strip()
    lines = response.split("\n")

    # Ensure proper formatting (fallback on failure)
    if not any("Calories" in line for line in lines):
        return f"Could not estimate nutrition for **{food.title()}**."

    return f"**{food.title()}**\n" + "\n".join(lines)

calorie_tool = StructuredTool.from_function(
    func=estimate_calorie,
    name="CalorieEstimatorTool",
    description="Estimates calories, protein, carbs, and fat per 100g or 1 serving for any food using GPT.",
    args_schema=CalorieInput
)
