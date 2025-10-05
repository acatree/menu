import pandas, os, requests, io, contextlib, traceback
import matplotlib.pyplot as plt
from pylatex import NoEscape
from openai_utils import ask_question

# -----------------------------
# 파일명 안전 처리
# -----------------------------
def safe_filename(section_title, suffix):
    mapping = {
        "서론": "intro",
        "관련 연구": "related",
        "연구 방법": "methods",
        "분석": "analysis",
        "결론": "conclusion"
    }
    name = mapping.get(section_title, ''.join(filter(str.isalnum, section_title)))
    return f"{name}_{suffix}.png"
# -----------------------------
# 이미지 생성
# -----------------------------
def generate_images(api_key, topic, section_title, count=1):
    import openai
    openai.api_key = api_key
    os.makedirs("images", exist_ok=True)
    image_files = []

    for i in range(count):
        prompt = f"'{topic}' '{section_title}' 섹션용 학술 시각 자료 생성"
        response = openai.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024")
        url = response.data[0].url
        img_data = requests.get(url).content
        filename = os.path.join("images", safe_filename(section_title, f"img{i+1}"))
        with open(filename, 'wb') as f:
            f.write(img_data)
        image_files.append(filename)

    return image_files

# -----------------------------
# 안정적인 matplotlib 그래프 생성
# -----------------------------
def generate_graph(section_title, topic, figure_number=1, language="ko", api_key=None):
    import numpy as np
    os.makedirs("graphs", exist_ok=True)
    fig_path = os.path.join("graphs", safe_filename(section_title, f"fig{figure_number}"))

    prompt = f"""
    Generate self-contained Python matplotlib code for the '{section_title}' section of '{topic}'.
    - Include data generation (e.g., x = [1,2,3], y = [4,5,6])
    - Use plt.figure() and plt.savefig(r'{fig_path}') to save the figure
    - Import necessary libraries (numpy as np)
    - Return only Python code, no explanations or comments
    """

    code = ask_question(prompt, language=language, api_key=api_key)

    try:
        local_env = {"plt": plt, "np": np}
        with contextlib.redirect_stdout(io.StringIO()):  # 모델 출력 무시
            exec(code, local_env)
        plt.close('all')
    except Exception as e:
        print(f"[그래프 생성 실패] {section_title}: {e}")
        traceback.print_exc()
        return ""
    return fig_path
# -----------------------------
# LaTeX figure 삽입
# -----------------------------
def insert_figure(doc, file_path, caption_text):
    doc.append(NoEscape(r"\begin{figure}[h]"))
    doc.append(NoEscape(r"\centering"))
    doc.append(NoEscape(f"\includegraphics[width=0.9\\textwidth]{{{file_path}}}"))
    doc.append(NoEscape(f"\caption{{{caption_text}}}"))
    doc.append(NoEscape(r"\end{figure}"))

def generate_table(section_title, topic, api_key=None):
    """
    주제 및 섹션에 맞는 간단한 표를 생성하여 LaTeX 표 형태로 반환
    """
    from .openai_utils import ask_question

    try:
        # OpenAI에게 표 생성 요청
        prompt = (
            f"'{topic}' 주제의 '{section_title}' 섹션을 위한 데이터 표를 작성해줘. "
            "3~5개의 열(column)과 5~10개의 행(row)을 가지며, "
            "수치형 데이터(숫자 포함)를 중심으로 작성하고, "
            "각 열 이름은 명확히 라벨링해줘. "
            "CSV 형식으로 출력해."
        )

        csv_text = ask_question(prompt, api_key=api_key)

        # CSV 형태로 파싱
        df = pd.read_csv(io.StringIO(csv_text))

        # LaTeX 표로 변환
        latex_table = df.to_latex(index=False, escape=False)
        return latex_table

    except Exception as e:
        print(f"[generate_table error] {e}")
        return None
