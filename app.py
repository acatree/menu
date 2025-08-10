from flask import Flask, render_template, request
import pandas as pd
from pulp import *

app = Flask(__name__)

# ===== 기본 데이터 =====
data = [
    {"name": "쌀밥", "cost": 0.5, "cal": 300, "protein": 6},
    {"name": "닭가슴살", "cost": 1.2, "cal": 165, "protein": 31},
    {"name": "계란", "cost": 0.3, "cal": 70, "protein": 6},
    {"name": "김치", "cost": 0.2, "cal": 20, "protein": 1},
    {"name": "두부찌개", "cost": 0.8, "cal": 180, "protein": 12},
    {"name": "된장국", "cost": 0.4, "cal": 80, "protein": 4},
    {"name": "멸치볶음", "cost": 0.5, "cal": 100, "protein": 10},
    {"name": "시금치나물", "cost": 0.3, "cal": 40, "protein": 3},
]
df = pd.DataFrame(data)

def optimize_menu(cal_target, protein_target, budget_limit):
    prob = LpProblem("MilitaryMealPlan", LpMinimize)
    menu_vars = LpVariable.dicts("servings", df["name"], lowBound=0, cat="Integer")

    # 비용 최소화
    prob += lpSum([menu_vars[i] * df.loc[df["name"] == i, "cost"].values[0] for i in df["name"]])

    # 제약조건
    prob += lpSum([menu_vars[i] * df.loc[df["name"] == i, "cal"].values[0] for i in df["name"]]) >= cal_target
    prob += lpSum([menu_vars[i] * df.loc[df["name"] == i, "protein"].values[0] for i in df["name"]]) >= protein_target
    prob += lpSum([menu_vars[i] * df.loc[df["name"] == i, "cost"].values[0] for i in df["name"]]) <= budget_limit

    prob.solve(PULP_CBC_CMD(msg=0))

    result = []
    total_cost, total_cal, total_protein = 0, 0, 0
    for i in df["name"]:
        qty = menu_vars[i].varValue
        if qty > 0:
            cost = qty * df.loc[df["name"] == i, "cost"].values[0]
            cal = qty * df.loc[df["name"] == i, "cal"].values[0]
            protein = qty * df.loc[df["name"] == i, "protein"].values[0]
            total_cost += cost
            total_cal += cal
            total_protein += protein
            result.append({"menu": i, "qty": int(qty), "cost": cost, "cal": cal, "protein": protein})

    return result, total_cost, total_cal, total_protein

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cal_target = int(request.form["cal"])
        protein_target = int(request.form["protein"])
        budget_limit = float(request.form["budget"])
        result, total_cost, total_cal, total_protein = optimize_menu(cal_target, protein_target, budget_limit)
        return render_template("index.html", result=result, total_cost=total_cost,
                               total_cal=total_cal, total_protein=total_protein)
    return render_template("index.html", result=None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
