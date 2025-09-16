import os
from pylatex import Document, Command, NoEscape
import openai
import subprocess
import ast

openai.api_key = None  # Flask에서 받은 API 키로 runtime에 세팅

def ask_question(question):
    response = openai.chat.completions.create(
        model="gpt-5-mini",
        #model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 친절한 한국어 작문 전문가입니다."},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()

def blogposting(topic):
    question = f"주제: [{topic}]\n800 단어 분량의 유튜브 숏 대본을 작성하세요. 반드시 한국어로 작성하세요."
    return ask_question(question)

def generate_latex(TOPIC1, num_list):
    question2 = f"'{TOPIC1}'와 관련된 서로 다른 {num_list}개의 소주제를 한국어 목록으로 제시하세요. 출력은 Python 리스트 형식으로 해주세요."
    try:
        content2 = ask_question(question2)
        topic_list = ast.literal_eval(content2)  # 안전하게 리스트 변환
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
