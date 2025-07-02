from typing import Literal
from pydantic import BaseModel
from langchain.tools import StructuredTool

class ProteinGoalInput(BaseModel):
    weight_kg: float
    goal: Literal["cut", "bulk", "maintain"]

def estimate_protein(weight_kg: float, goal: str) -> str:
    multiplier = {"cut": 2.0, "bulk": 1.6, "maintain": 1.2}[goal]
    grams = weight_kg * multiplier
    return f"🎯 Goal: {goal}\n🧍 Weight: {weight_kg} kg\n🥩 Protein: {grams:.1f}g/day ({multiplier}g/kg)"

protein_goal_tool = StructuredTool.from_function(
    func=estimate_protein,
    name="ProteinGoalEstimatorTool",
    description="Calculate daily protein need based on weight and goal.",
    args_schema=ProteinGoalInput
)
