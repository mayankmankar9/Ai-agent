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
    week_foods = []
    day_food_lists = []
    margin = 50  # kcal margin for target
    warning = None
    
    # Generate each day's plan using the improved meal planner
    week_plan = []
    total_cal, total_pro, total_carb, total_fat = 0, 0, 0, 0
    
    for day in range(1, 8):
        retries = 0
        day_result = None
        
        while retries < 3:
            result = plan_meal(goal, diet_type, calorie_target, protein_target, dislikes)
            
            # Parse total calories from result to check if within margin
            try:
                total_line = [l for l in result.split("\n") if l.startswith("Total:")][0]
                cal = float(total_line.split(":")[1].split("kcal")[0].strip())
                if abs(cal - calorie_target) <= margin:
                    day_result = result
                    break
            except Exception as e:
                print(f"⚠️ Error parsing day {day} result: {e}")
                pass
            retries += 1
        
        if day_result is None:
            # Use the last attempt even if not within margin
            day_result = result
            if warning is None:
                warning = f"⚠️ Could not generate meal plans within ±{margin} kcal of the target after 3 attempts for some days."
        
        # Parse macros for weekly summary
        try:
            total_line = [l for l in day_result.split("\n") if l.startswith("Total:")][0]
            # Parse format: "Total: 1234.5 kcal, 56.7g protein, 123.4g carbs, 45.6g fat"
            parts = total_line.split(":")
            if len(parts) > 1:
                macro_parts = parts[1].split(",")
                
                # Extract calories
                cal = float(macro_parts[0].replace("kcal", "").strip())
                total_cal += cal
                
                # Extract protein
                if len(macro_parts) > 1:
                    pro = float(macro_parts[1].replace("g protein", "").strip())
                    total_pro += pro
                
                # Extract carbs
                if len(macro_parts) > 2:
                    carb = float(macro_parts[2].replace("g carbs", "").strip())
                    total_carb += carb
                
                # Extract fat
                if len(macro_parts) > 3:
                    fat = float(macro_parts[3].replace("g fat", "").strip())
                    total_fat += fat
                    
        except Exception as e:
            print(f"⚠️ Error parsing macros for day {day}: {e}")
            pass
        
        week_plan.append(f"📅 Day {day}:\n{day_result.strip()}")
    
    # Add warning if needed
    if warning:
        week_plan.append(warning)
    
    # Weekly summary
    week_plan.append(f"\n📊 Weekly Summary:")
    week_plan.append(f"Total: {total_cal:.1f} kcal, {total_pro:.1f}g protein, {total_carb:.1f}g carbs, {total_fat:.1f}g fat")
    week_plan.append(f"Daily Average: {total_cal/7:.1f} kcal, {total_pro/7:.1f}g protein, {total_carb/7:.1f}g carbs, {total_fat/7:.1f}g fat")
    
    return "\n\n".join(week_plan)

weekly_planner_tool = StructuredTool.from_function(
    func=generate_weekly_plan,
    name="WeeklyPlannerTool",
    description="Create a 7-day varied meal plan based on user's nutrition goal.",
    args_schema=WeeklyPlannerInput
)
