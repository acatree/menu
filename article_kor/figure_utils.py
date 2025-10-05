import os, requests, io, contextlib
import matplotlib.pyplot as plt
from pylatex import NoEscape

def safe_filename(section_title, suffix):
    mapping = {
        "서론": "intro",
        "관련 연구": "related",
        "연구 방법": "methods",
        "실험 및 결과": "results",
        "논의": "discussion",
        "결론": "conclusion"
    }
    name = mapping.get(section_title, ''.join(filter(str.isalnum, section_title)))
    return f"{name}_{suffix}.png"

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

def generate_graph(section_title, topic, figure_number=1, language="ko", api_key=None):
    import openai
    openai.api_key = api_key
    os.makedirs("graphs", exist_ok=True)
    fig_path = os.path.join("graphs", safe_filename(section_title, f"fig{figure_number}"))
    question = f"'{topic}' '{section_title}' 섹션용 matplotlib 코드 생성, plt.savefig('{fig_path}') 포함"
    code = openai_utils.ask_question(question, language, api_key)
    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            exec(code, {"plt": plt})
        plt.close()
    except Exception as e:
        print(f"[그래프 생성 실패] {section_title}: {e}")
        return ""
    return fig_path

def insert_figure(doc, file_path, caption_text):
    doc.append(NoEscape(r"\begin{figure}[h]"))
    doc.append(NoEscape(r"\centering"))
    doc.append(NoEscape(f"\includegraphics[width=0.9\\textwidth]{{{file_path}}}"))
    doc.append(NoEscape(f"\caption{{{caption_text}}}"))
    doc.append(NoEscape(r"\end{figure}"))
