# ebook.py

import os
import csv
from pylatex import Document, Command, NoEscape
import openai
from config import OPENAI_API_KEY
import subprocess

openai.api_key = OPENAI_API_KEY

# --- OpenAI helper functions ---

def ask_question(question):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 친절한 한국어 작문 전문가입니다."},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()

def blogposting(topic):
    question = f"주제: [{topic}]\n200 단어 분량의 유튜브 숏 대본을 작성하세요. 반드시 한국어로 작성하세요."
    return ask_question(question)

# --- LaTeX + PDF generation ---
def generate_latex(TOPIC1, num_list):
    """
    Generates LaTeX + PDF file for the topic and returns paths.
    """
    # 소주제 리스트 생성
    question2 = f"'{TOPIC1}'와 관련된 서로 다른 {num_list}개의 소주제를 한국어 목록으로 제시하세요. 출력은 Python 리스트 형식으로 해주세요."
    try:
        content2 = ask_question(question2)
        topic_list = eval(content2)  # expects Python list format
    except:
        topic_list = [TOPIC1 + f" 소주제 {i+1}" for i in range(num_list)]

    to_list = topic_list[:num_list]

    # LaTeX 문서 작성
    document = Document(documentclass='scrbook', document_options=['a5paper', 'pagesize', '10pt'])
    document.preamble.append(Command('usepackage', 'kotex'))

    # 표지
    title = f"{TOPIC1} 전자책"
    subtitle = f"{TOPIC1} 관련 소주제"
    document.append(NoEscape(r"\begin{titlepage}"))
    document.append(NoEscape(f"\\centering{{\\fontsize{{30}}{{48}}\\selectfont {title}}}\\\\"))
    document.append(NoEscape(f"\\centering{{\\fontsize{{18}}{{48}}\\selectfont {subtitle}}}\\\\"))
    document.append(NoEscape(r"\end{titlepage}"))

    # 본문
    for ii, topic in enumerate(to_list):
        sectiontitle = f"\\section*{{{ii+1}. {topic}}}"
        document.append(NoEscape(sectiontitle))
        content = blogposting(topic)
        document.append(NoEscape(r"\large{" + content + "}"))
        document.append(Command('newpage'))

    # 저장 경로
    tex_folder = 'tex'
    os.makedirs(tex_folder, exist_ok=True)
    tex_path = os.path.join(tex_folder, f"{TOPIC1}.tex")
    pdf_path = tex_path.replace(".tex", ".pdf")

    # .tex 저장
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(document.dumps())

    # PDF 변환 실행
    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", tex_folder, tex_path],
            check=True
        )
    except Exception as e:
        print("PDF 변환 실패:", e)

    return tex_path, pdf_path
