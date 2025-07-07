from app.firebase import get_user_profile, save_weekly_plan
from app.tools.calorie_tool import calorie_tool
from app.tools.meal_planner_tool import meal_planner_tool
from app.tools.protein_goal_tool import protein_goal_tool, estimate_protein
from app.tools.tdee_calculator_tool import tdee_calculator_tool, calculate_tdee
from app.tools.weekly_planner_tool import weekly_planner_tool, generate_weekly_plan
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType

import re

# 🧠 Use GPT-3.5-turbo
llm = ChatOpenAI(model="gpt-3.5-turbo")

def run_multiweek_plan(user_id: str, query: str) -> str:
    user = get_user_profile(user_id)
    if not user:
        return "❌ User profile not found."

    # Validate required fields
    required_fields = [
        "goal", "goal_intensity", "diet_type", "weight_kg", "height_cm", "age", "gender", "activity_level", "tenure_months", "target_weight"
    ]
    for field in required_fields:
        if field not in user or user[field] in [None, ""]:
            return f"❌ Missing required field: {field}. Please complete your profile."

    goal = user.get("goal")
    goal_intensity = user.get("goal_intensity", "balanced")
    diet_type = user.get("diet_type")
    dislikes = user.get("dislikes", "")
    weight = float(user.get("weight_kg"))
    height = float(user.get("height_cm"))
    age = int(user.get("age"))
    gender = user.get("gender")
    activity = user.get("activity_level")
    tenure = int(user.get("tenure_months") or 3)
    target_weight = float(user.get("target_weight"))

    # ⚙️ Step 1: BMR & TDEE
    tdee_data = calculate_tdee(gender, age, weight, height, activity)
    try:
        tdee_val = float(tdee_data.split("TDEE:")[1].split("kcal")[0].strip())
    except:
        return "❌ Could not parse TDEE."

    # 🎯 Step 2: Protein Goal
    protein_val = float(estimate_protein(weight, goal).split("Protein:")[1].split("g/")[0].strip())

    # 🔥 Step 3: Calorie target with goal_intensity
    if goal == "maintain":
        calorie_target = tdee_val
    else:
        adjustment = {
            "conservative": 250,
            "balanced": 500,
            "aggressive": 750
        }.get(goal_intensity, 500)
        calorie_target = tdee_val + adjustment if goal == "bulk" else tdee_val - adjustment

    # 📆 Step 4: Calculate weekly loop
    current_weight = weight
    weeks = []
    direction = 1 if goal == "bulk" else -1 if goal == "cut" else 0
    max_weeks = tenure * 4
    week_num = 1

    if direction == 0:
        return "ℹ️ Maintenance plans are generated only for 4 weeks."

    while week_num <= max_weeks:
        # Stop if weight goal is hit
        if (direction == -1 and current_weight <= target_weight) or (direction == 1 and current_weight >= target_weight):
            break

        # 🔁 Weekly meal generation
        result = generate_weekly_plan(
            goal=goal,
            diet_type=diet_type,
            calorie_target=calorie_target,
            protein_target=protein_val,
            dislikes=dislikes,
            user_id=user_id
        )

        # Parse macros
        macro_match = re.search(r"Weekly Total: ([\d.]+) kcal, ([\d.]+)g protein, ([\d.]+)g carbs, ([\d.]+)g fat", result)
        if not macro_match:
            break

        week_cals, week_pro, week_carb, week_fat = map(float, macro_match.groups())

        # Estimate weight change (1kg fat ≈ 7700 kcal)
        delta_kg = (week_cals - tdee_val * 7) / 7700.0
        projected_weight = current_weight + delta_kg

        # Cap projected weight
        if direction == -1 and projected_weight < target_weight:
            projected_weight = target_weight
        elif direction == 1 and projected_weight > target_weight:
            projected_weight = target_weight

        # Collect warnings if needed
        warnings = []
        if abs(delta_kg) > 1.5:
            warnings.append(
                f"⚠️ Week {week_num}: Projected weight change ({delta_kg:+.2f}kg) is aggressive."
            )

        # Store to Firestore
        save_weekly_plan(
            user_id=user_id,
            week_number=week_num,
            start_weight=current_weight,
            end_weight=projected_weight,
            calories=week_cals,
            protein=week_pro,
            carbs=week_carb,
            fat=week_fat,
            response=result,
            warnings=warnings
        )

        # Append formatted string
        weeks.append(
            f"\n===== Week {week_num} =====\n"
            f"Start Weight: {current_weight:.1f}kg\n{result}\nEnd Weight: {projected_weight:.1f}kg"
        )

        # Update for next week
        current_weight = projected_weight
        week_num += 1

    if not weeks:
        return "❌ No valid meal plans generated. Please check your profile settings."

    return "\n".join(weeks)

# 🤖 Entry point for user interaction
def run_agent(user_id: str, query: str) -> str:
    if "multiweek" in query.lower() or "tenure" in query.lower() or "full plan" in query.lower():
        return run_multiweek_plan(user_id, query)

    user = get_user_profile(user_id)
    if not user:
        return "❌ User profile not found."

    # Validate required fields
    required_fields = [
        "goal", "goal_intensity", "diet_type", "weight_kg", "height_cm", "age", "gender", "activity_level", "tenure_months", "target_weight"
    ]
    for field in required_fields:
        if field not in user or user[field] in [None, ""]:
            return f"❌ Missing required field: {field}. Please complete your profile."

    full_query = build_user_prompt(user_id, query)
    tools = [
        calorie_tool,
        meal_planner_tool,
        protein_goal_tool,
        tdee_calculator_tool,
        weekly_planner_tool
    ]
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True
    )
    return agent.run(full_query)

def build_user_prompt(user_id: str, query: str) -> str:
    user = get_user_profile(user_id)
    if not user:
        return query
    tdee = calculate_tdee(user["gender"], user["age"], user["weight_kg"], user["height_cm"], user["activity_level"])
    protein = estimate_protein(user["weight_kg"], user["goal"])
    return f"""
User Profile:
- Goal: {user.get("goal")}
- Intensity: {user.get("goal_intensity", "balanced")}
- Diet Type: {user.get("diet_type")}
- Dislikes: {user.get("dislikes")}
- Age: {user.get("age")}, Gender: {user.get("gender")}
- Weight: {user.get("weight_kg")} → Target: {user.get("target_weight")}
- Height: {user.get("height_cm")} cm
- Tenure: {user.get("tenure_months")} months
- Activity: {user.get("activity_level")}

Estimated TDEE:
{tdee}

Estimated Protein Goal:
{protein}

Query:
{query}
""".strip()
