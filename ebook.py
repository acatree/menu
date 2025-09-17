import os
from pylatex import Document, Command, NoEscape
import openai
import subprocess
import ast
import json

openai.api_key = None  # Flask에서 받은 API 키로 runtime에 세팅
def ask_question(question):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # 또는 gpt-3.5-turbo 등 최신 모델
        messages=[
            {"role": "system", "content": "당신은 친절한 한국어 작문 전문가입니다."},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_completion_tokens=1024,  # ⚠ 여기만 바뀜
    )
    return response.choices[0].message.content.strip()

def blogposting(topic):
    question = f"주제: [{topic}]\n500 단어 분량의 관련된 글을 작성하세요. 전문적이고 친절한 문체로 작성 할 것이고 반드시 한국어로 작성하세요."
    return ask_question(question)

def generate_latex(TOPIC1, num_list):
    question2 = f"""
           '{TOPIC1}'와 관련된 서로 다른 {num_list}개의 소주제를 
           반드시 JSON 배열 형식으로 출력하세요.
           예: ["주제1", "주제2", "주제3"]
           다른 설명, 문장, 글자, 쉼표 없이 배열만 반환하세요.
           """
    content2 = ask_question(question2)
    try:
        topic_list = json.loads(content2)
    except:
        topic_list = [TOPIC1 + f" 소주제 {i+1}" for i in range(num_list)]

    to_list = topic_list[:num_list]
    document = Document(documentclass='scrbook', document_options=['a5paper', 'pagesize', '10pt'])
    document.preamble.append(Command('usepackage', 'kotex'))

    title = f"{TOPIC1} 전자책"
    subtitle = f"{TOPIC1} 관련 소주제"
    document.append(NoEscape(r"\begin{titlepage}"))
    document.append(NoEscape(f"\\centering{{\\fontsize{{30}}{{48}}\\selectfont {title}}}\\\\"))
    document.append(NoEscape(f"\\centering{{\\fontsize{{18}}{{48}}\\selectfont {subtitle}}}\\\\"))
    document.append(NoEscape(r"\end{titlepage}"))

    for ii, topic in enumerate(to_list):
        sectiontitle = f"\\section*{{{ii+1}. {topic}}}"
        document.append(NoEscape(sectiontitle))
        content = blogposting(topic)
        document.append(NoEscape(r"\large{" + content + "}"))
        document.append(Command('newpage'))

    tex_folder = 'tex'
    os.makedirs(tex_folder, exist_ok=True)
    tex_path = os.path.join(tex_folder, f"{TOPIC1}.tex")
    pdf_path = tex_path.replace(".tex", ".pdf")

    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(document.dumps())

    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", tex_folder, tex_path],
            check=True
        )
    except Exception as e:
        print("PDF 변환 실패:", e)

    return tex_path, pdf_path
