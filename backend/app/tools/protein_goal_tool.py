from typing import Literal
from pydantic import BaseModel
from langchain.tools import StructuredTool

# Input schema for protein goal tool
class ProteinGoalInput(BaseModel):
    weight_kg: float
    goal: Literal["cut", "bulk", "maintain"]

# Core logic
def estimate_protein(weight_kg: float, goal: str) -> dict:
    # Protein requirement multipliers
    multiplier = {
        "cut": 2.0,       # Higher to preserve muscle during deficit
        "bulk": 1.6,      # Slightly lower, assuming surplus helps retention
        "maintain": 1.2   # Moderate for upkeep
    }[goal]

    grams = round(weight_kg * multiplier, 1)

    return {
        "goal": goal,
        "weight_kg": weight_kg,
        "protein_per_kg": multiplier,
        "protein_grams_per_day": grams
    }

# Wrap in LangChain StructuredTool
protein_goal_tool = StructuredTool.from_function(
    func=estimate_protein,
    name="ProteinGoalEstimatorTool",
    description="Calculate daily protein need (g/day) based on weight and goal.",
    args_schema=ProteinGoalInput
)
