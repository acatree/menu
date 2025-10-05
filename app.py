from flask import Flask, render_template, request, send_file
import pandas as pd
from pulp import *
import os
from ebook import generate_latex, openai
import subprocess
import youtube
from openai import OpenAI
import os, zipfile
from io import BytesIO

app = Flask(__name__)


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

@app.route("/index0", methods=["GET", "POST"])
def index0():
    return render_template("index0.html")

@app.route("/index2", methods=["GET", "POST"])
def index2():
    if request.method == "POST":
        apikey = request.form.get("apikey")
        topic = request.form.get("topic")
        num_list = request.form.get("num_list")
        filetype = request.form.get("filetype")

        if not apikey or not topic or not num_list:
            return render_template("index2.html", error="⚠ API 키, 주제, 하위 주제 개수를 모두 입력하세요.")

        try:
            num_list = int(num_list)
        except ValueError:
            return render_template("index2.html", error="⚠ 하위 주제 개수는 정수여야 합니다.")

        openai.api_key = apikey  # 사용자 입력 API 키 세팅

        tex_path, pdf_path = generate_latex(topic, num_list)

        if filetype == "pdf":
            if os.path.exists(pdf_path):
                return send_file(pdf_path, as_attachment=True)
            else:
                return render_template("index2.html", error="⚠ PDF 생성에 실패했습니다.")
        else:
            return send_file(tex_path, as_attachment=True)

    return render_template("index2.html")

@app.route("/index3", methods=["GET", "POST"])
def index3():
    return render_template("index3.html")

@app.route("/generate", methods=["POST"])
def generate():
    api_key = request.form["api_key"]
    topic = request.form["topic"]
    num_images = int(request.form["num_images"])

    try:
        output_file = youtube.create_youtube_short(api_key, topic, num_images)
        # 자동 다운로드
        return send_file(output_file, as_attachment=True)
    except Exception as e:
        return f"<h2>에러 발생</h2><pre>{e}</pre>"


@app.route("/index6", methods=["GET", "POST"])
def index6():
    return render_template("index6.html")

@app.route("/index7", methods=["GET", "POST"])
def index7():
    error = None
    if request.method == "POST":
        try:
            apikey = request.form.get("apikey")
            client = OpenAI(api_key=apikey)

            title = request.form.get("title")
            topic = request.form.get("topic")
            references = int(request.form.get("references", 10))
            language = request.form.get("language", "ko")

            # 언어별 논문 생성기 선택
            if language == "ko":
                from article_kor import generate_paper
            else:
                from article_eng import generate_paper

            # 논문 생성
            generated_files = generate_paper(
                title, topic, language=language, references=references, client=client
            )

            # ZIP 파일로 묶기
            memory_file = BytesIO()
            with zipfile.ZipFile(memory_file, "w") as zf:
                for file_path in generated_files:
                    zf.write(file_path, os.path.basename(file_path))
            memory_file.seek(0)

            return send_file(
                memory_file,
                download_name=f"{title}.zip",
                as_attachment=True,
            )

        except Exception as e:
            error = str(e)

    return render_template("index7.html", error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
