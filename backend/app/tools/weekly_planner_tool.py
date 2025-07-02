from typing import Literal, Optional
from pydantic import BaseModel
from langchain.tools import StructuredTool
from app.tools.meal_planner_tool import plan_meal
from app.firebase import get_used_foods, update_used_foods

class WeeklyPlannerInput(BaseModel):
    goal: Literal["cut", "bulk", "maintain"]
    diet_type: Literal["veg", "non-veg"]
    calorie_target: float
    protein_target: float
    dislikes: Optional[str] = None
    user_id: Optional[str] = None

def generate_weekly_plan(goal, diet_type, calorie_target, protein_target, dislikes=None, user_id=None):
    used_foods = get_used_foods(user_id) if user_id else []
    week_plan = []

    for day in range(1, 8):
        full_dislikes = (dislikes or "") + ", " + ", ".join(used_foods)
        result = plan_meal(goal, diet_type, calorie_target, protein_target, full_dislikes)

        week_plan.append(f"📅 Day {day}:\n{result.strip()}")

        for line in result.split("\n"):
            if "→" in line:
                food = line.split("→")[0].strip("- ").strip()
                used_foods.append(food)

        if user_id:
            update_used_foods(user_id, used_foods)

    return "\n\n".join(week_plan)

weekly_planner_tool = StructuredTool.from_function(
    func=generate_weekly_plan,
    name="WeeklyPlannerTool",
    description="Create a 7-day varied meal plan based on user's nutrition goal.",
    args_schema=WeeklyPlannerInput
)
