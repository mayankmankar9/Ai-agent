from app.firebase import get_user_profile
from app.tools.calorie_tool import calorie_tool
from app.tools.meal_planner_tool import meal_planner_tool
from app.tools.protein_goal_tool import protein_goal_tool, estimate_protein
from app.tools.tdee_calculator_tool import tdee_calculator_tool, calculate_tdee
from app.tools.weekly_planner_tool import weekly_planner_tool
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

# 🔧 Main agent runner
def run_agent(user_id: str, query: str) -> str:
    user = get_user_profile(user_id)
    if not user:
        return "❌ User profile not found."

    # Build personalized prompt context
    full_query = build_user_prompt(user_id, query)

    # 🔌 Initialize agent with tools
    tools = [
        calorie_tool,
        meal_planner_tool,
        protein_goal_tool,
        tdee_calculator_tool,
        weekly_planner_tool
    ]
    llm = ChatOpenAI(model="gpt-4")  # Or "gpt-3.5-turbo" if preferred

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    # 💬 Run the query through agent
    response = agent.run(full_query)
    return response


# ✍️ Build user profile context for prompt
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
