from flask import Flask, render_template, request, send_file
import pandas as pd
from pulp import *
import os
from ebook import generate_latex        

app = Flask(__name__)
# ===== 기본 데이터 =====
# 데이터 파일 경로
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "menu_data.csv")
# 데이터 읽기 함수
def load_data():
    return pd.read_csv(DATA_PATH)

def optimize_menu(cal_target, protein_target, budget_limit):
    df = load_data()  # 매번 최신 데이터 읽기
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

@app.route("/index2", methods=["GET", "POST"])
def index2():
    if request.method == "POST":
        topic = request.form.get("topic")
        num_list = request.form.get("num_list")
        filetype = request.form.get("filetype")  # tex or pdf

        if not topic or not num_list:
            return render_template("index2.html", error="⚠ 주제와 하위 주제 개수를 모두 입력하세요.")

        try:
            num_list = int(num_list)
        except ValueError:
            return render_template("index2.html", error="⚠ 하위 주제 개수는 정수여야 합니다.")

        # 1️⃣ LaTeX 파일 생성
        tex_path, pdf_path = generate_latex(topic, num_list)  # 수정 필요: generate_latex이 pdf_path도 반환하도록

        if filetype == "pdf":
            try:
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", os.path.dirname(tex_path), tex_path],
                    check=True
                )
                return send_file(pdf_path, as_attachment=True)
            except subprocess.CalledProcessError as e:
                print(e)
                return render_template("index2.html", error="⚠ PDF 생성에 실패했습니다.")
        else:
            return send_file(tex_path, as_attachment=True)

    # GET 요청 시
    return render_template("index2.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
