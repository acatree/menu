import os, requests, io, contextlib, traceback
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
