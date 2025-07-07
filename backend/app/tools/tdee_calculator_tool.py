from typing import Literal
from pydantic import BaseModel
from langchain.tools import StructuredTool

# Input schema for the TDEE calculator
class TDEEInput(BaseModel):
    gender: Literal["male", "female"]
    age: int
    weight_kg: float
    height_cm: float
    activity_level: Literal["sedentary", "moderate", "very active"]

# Main TDEE calculation function
def calculate_tdee(
    gender: str,
    age: int,
    weight_kg: float,
    height_cm: float,
    activity_level: str
) -> dict:
    # Step 1: Calculate BMR using Mifflin-St Jeor equation
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if gender == "male" else -161)

    # Step 2: Get TDEE multiplier based on activity level
    activity_map = {
        "sedentary": 1.2,
        "moderate": 1.55,
        "very active": 1.9
    }
    level = activity_level.strip().lower()
    multiplier = activity_map.get(level)
    if multiplier is None:
        return {
            "error": f"Unknown activity level '{activity_level}'. Please use one of: sedentary, moderate, very active."
        }

    # Step 3: Calculate TDEE
    tdee = bmr * multiplier

    # Step 4: Return structured output for downstream tools
    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "calorie_multiplier": multiplier
    }

# Register as a LangChain StructuredTool
tdee_calculator_tool = StructuredTool.from_function(
    func=calculate_tdee,
    name="TDEECalculatorTool",
    description="Estimate BMR and TDEE using weight, height, age, gender, and activity level.",
    args_schema=TDEEInput
)
