from typing import Literal, Optional
from pydantic import BaseModel
from langchain.tools import StructuredTool
from app.tools.meal_planner_tool import plan_meal
from app.firebase import get_used_foods, update_used_foods, save_weekly_plan
from firebase_admin import firestore
from datetime import datetime

class WeeklyPlannerInput(BaseModel):
    goal: Literal["cut", "bulk", "maintain"]
    diet_type: Literal["veg", "non-veg"]
    calorie_target: float
    protein_target: float
    current_weight: float
    target_weight: Optional[float] = None
    dislikes: Optional[str] = None
    user_id: Optional[str] = None

def parse_macros_from_summary(summary: str):
    import re
    match = re.search(r"Total: ([\d.]+) kcal, ([\d.]+)g protein, ([\d.]+)g carbs, ([\d.]+)g fat", summary)
    if match:
        return tuple(float(x) for x in match.groups())
    return (0.0, 0.0, 0.0, 0.0)

def estimate_tenure_weeks(current_weight: float, target_weight: float, goal: str) -> int:
    if goal == "bulk":
        rate = 0.25  # kg per week
    elif goal == "cut":
        rate = 0.5  # kg per week
    else:
        return 4
    weight_diff = abs(target_weight - current_weight)
    return max(1, round(weight_diff / rate))

def get_last_completed_week(user_id: str) -> int:
    db = firestore.client()
    plans_ref = db.collection("users").document(user_id).collection("plans")
    weeks = plans_ref.stream()
    week_nums = [int(doc.id.split("_")[-1]) for doc in weeks if doc.id.startswith("week_")]
    return max(week_nums) if week_nums else 0

def log_week_to_firestore(user_id: str, week_num: int, data: dict):
    db = firestore.client()
    week_ref = db.collection("users").document(user_id).collection("plans").document(f"week_{week_num}")
    data["generated_at"] = datetime.utcnow().isoformat()
    week_ref.set(data)

def generate_weekly_plan(goal, diet_type, calorie_target, protein_target,
                          current_weight, target_weight=None, dislikes=None, user_id=None):
    used_meals = set(get_used_foods(user_id))  # Fetch previously used meals
    weekly_meals = []
    total_weeks = estimate_tenure_weeks(current_weight, target_weight, goal) if target_weight else 4
    weeks_to_generate = min(total_weeks, 4)

    monthly_plan = []
    last_week = get_last_completed_week(user_id) if user_id else 0
    projected_weight = current_weight

    for week_offset in range(weeks_to_generate):
        week_num = last_week + week_offset + 1
        week_plan = []
        week_cal, week_pro, week_carb, week_fat = 0, 0, 0, 0
        warnings = []

        for day in range(1, 8):
            full_dislikes = (dislikes or "") + ", " + ", ".join(used_meals)
            result = plan_meal(goal, diet_type, calorie_target, protein_target, full_dislikes)
            cal, pro, carb, fat = parse_macros_from_summary(result)

            if cal == 0 or pro == 0:
                warnings.append(f"⚠️ Week {week_num} Day {day}: Could not generate valid meal plan. Skipped.")
                continue

            week_cal += cal
            week_pro += pro
            week_carb += carb
            week_fat += fat
            week_plan.append(f"📅 Week {week_num} - Day {day}:\n{result.strip()}")

            for line in result.split("\n"):
                if "→" in line:
                    food = line.split("→")[0].strip("- ").strip()
                    if food in used_meals:
                        continue  # Skip duplicate
                    weekly_meals.append(food)
                    used_meals.add(food)

            if user_id:
                update_used_foods(user_id, list(used_meals))

        if goal == "bulk":
            expected_change = 0.25
        elif goal == "cut":
            expected_change = -0.5
        else:
            expected_change = 0.0

        start_weight = projected_weight
        projected_weight += expected_change

        week_summary = (f"\n\n🧮 Week {week_num} Summary:\nTotal: {week_cal:.1f} kcal, {week_pro:.1f}g protein, "
                        f"{week_carb:.1f}g carbs, {week_fat:.1f}g fat"
                        f"\nExpected weight change: {expected_change:+.2f} kg"
                        f"\nProjected weight: {projected_weight:.1f} kg")

        if warnings:
            week_summary += "\n" + "\n".join(warnings)

        if user_id:
            log_week_to_firestore(user_id, week_num, {
                "start_weight": start_weight,
                "end_weight": projected_weight,
                "calories": week_cal,
                "protein": week_pro,
                "carbs": week_carb,
                "fat": week_fat,
                "warnings": warnings,
                "foods_used": list(used_meals)[-15:]
            })
            save_weekly_plan(user_id, week_num, start_weight, projected_weight, week_cal, week_pro, week_carb, week_fat, warnings, "\n\n".join(week_plan) + week_summary, meals=weekly_meals)

        monthly_plan.append("\n\n".join(week_plan) + week_summary)

    return "\n\n==============================\n\n".join(monthly_plan)


weekly_planner_tool = StructuredTool.from_function(
    func=generate_weekly_plan,
    name="WeeklyPlannerTool",
    description="Generate a 4-week meal plan based on nutrition goals, tracking weekly progress and projecting weight.",
    args_schema=WeeklyPlannerInput
)
