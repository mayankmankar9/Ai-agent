from app.firebase import get_user_profile
from app.tools.calorie_tool import calorie_tool
from app.tools.meal_planner_tool import meal_planner_tool
from app.tools.protein_goal_tool import protein_goal_tool, estimate_protein
from app.tools.tdee_calculator_tool import tdee_calculator_tool, calculate_tdee
from app.tools.weekly_planner_tool import weekly_planner_tool

from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI


def run_agent(user_id: str, query: str) -> str:
    user = get_user_profile(user_id)
    if not user:
        return "❌ User profile not found."

    full_query = build_user_prompt(user_id, query)

    tools = [
        calorie_tool,
        meal_planner_tool,
        protein_goal_tool,
        tdee_calculator_tool,
        weekly_planner_tool,
    ]

    llm = ChatOpenAI(model="gpt-4")

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS,  # ✅ Supports multi-input tools
        verbose=True,
    )

    response = agent.run(full_query)
    return response


def build_user_prompt(user_id: str, query: str) -> str:
    user = get_user_profile(user_id)
    if not user:
        return query

    goal = user.get("goal")
    diet_type = user.get("diet_type")
    dislikes = user.get("dislikes", "")
    weight = user.get("weight_kg")
    height = user.get("height_cm")
    age = user.get("age")
    gender = user.get("gender")
    activity = user.get("activity_level")
    tenure = user.get("tenure_months")
    target_weight = user.get("target_weight")

    tdee = calculate_tdee(gender, age, weight, height, activity)
    protein = estimate_protein(weight, goal)

    return f"""
User Profile:
- Name: {user.get('name', 'Unknown')}
- Goal: {goal}
- Diet Type: {diet_type}
- Dislikes: {dislikes}
- Weight: {weight}kg → Target: {target_weight or 'Not specified'}
- Tenure: {tenure or 'Not specified'} months
- Gender: {gender}
- Age: {age}
- Height: {height} cm
- Activity Level: {activity}

Estimated Needs:
{tdee}

Protein Goal:
{protein}

User Query:
{query}
""".strip()


def parse_nutrition_from_meal(meal_text: str) -> Dict[str, float]:
    # Parses a meal plan string and sums up kcal, protein, carbs, fat for the week
    import re
    kcal, protein, carbs, fat = 0, 0, 0, 0
    for line in meal_text.splitlines():
        # Look for lines like: Calories: 123, Protein: 12, Carbs: 34, Fat: 5
        if 'Calories:' in line and 'Protein:' in line:
            try:
                kcal += float(re.search(r'Calories: ([\d.]+)', line).group(1))
                protein += float(re.search(r'Protein: ([\d.]+)', line).group(1))
                carbs += float(re.search(r'Carbs: ([\d.]+)', line).group(1))
                fat += float(re.search(r'Fat: ([\d.]+)', line).group(1))
            except Exception:
                continue
    return {"kcal": kcal, "protein": protein, "carbs": carbs, "fat": fat}


def generate_multiweek_plan(user_id: str, tenure_months: int) -> Dict[str, Any]:
    user = get_user_profile(user_id)
    if not user:
        return {"error": "User profile not found."}

    goal = user.get("goal")
    diet_type = user.get("diet_type")
    dislikes = user.get("dislikes", "")
    weight = float(user.get("weight_kg"))
    height = float(user.get("height_cm"))
    age = int(user.get("age"))
    gender = user.get("gender")
    activity = user.get("activity_level")
    target_weight = user.get("target_weight")

    weeks = tenure_months * 4
    plans = []
    cumulative = {"kcal": 0, "protein": 0, "carbs": 0, "fat": 0}
    current_weight = weight
    kcal_per_kg = 7700  # Roughly 7700 kcal = 1kg fat

    for week in range(1, weeks + 1):
        # Calculate TDEE for current week
        tdee_str = calculate_tdee(gender, age, current_weight, height, activity)
        tdee_val = float([line for line in tdee_str.split("\n") if "TDEE" in line][0].split(":")[1].split()[0])
        # Calculate protein goal for current week
        protein_goal_str = estimate_protein(current_weight, goal)
        protein_goal_val = float([line for line in protein_goal_str.split("\n") if "Protein" in line][0].split(":")[1].split("g")[0])
        # Generate weekly plan (as a string)
        week_plan = weekly_planner_tool.invoke({
            "goal": goal,
            "diet_type": diet_type,
            "calorie_target": tdee_val,
            "protein_target": protein_goal_val,
            "dislikes": dislikes,
            "user_id": user_id
        })
        # Parse nutrition totals
        totals = parse_nutrition_from_meal(week_plan)
        for k in cumulative:
            cumulative[k] += totals[k]
        # Simulate weight change
        kcal_diff = totals["kcal"] - (tdee_val * 7)
        weight_change = kcal_diff / kcal_per_kg
        next_weight = current_weight + weight_change
        plans.append({
            "week": week,
            "plan": week_plan,
            "totals": totals,
            "start_weight": current_weight,
            "end_weight": next_weight,
            "tdee": tdee_val,
            "protein_goal": protein_goal_val
        })
        current_weight = next_weight
    # Cumulative summary
    summary = {
        "total_kcal": cumulative["kcal"],
        "total_protein": cumulative["protein"],
        "total_carbs": cumulative["carbs"],
        "total_fat": cumulative["fat"],
        "start_weight": weight,
        "end_weight": current_weight,
        "weeks": weeks
    }
    return {"weeks": plans, "summary": summary}
