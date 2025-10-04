import os
from pylatex import Document, Command, NoEscape
import openai
import matplotlib.pyplot as plt
import contextlib
import io

openai.api_key = None  # Flask 또는 환경변수에서 세팅

# ---------------------------
# ChatGPT 요청 함수
# ---------------------------
def ask_question(question, language="ko"):
    system_prompt = "당신은 SCI/KCI 수준 학술 논문 작성 전문가입니다." if language=="ko" else "You are an expert in academic paper writing."
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_completion_tokens=3000,
    )
    return response.choices[0].message.content.strip()

# ---------------------------
# 섹션 작성
# ---------------------------
def write_section(title, topic, language="ko"):
    question = f"'{topic}' 주제에 대해 '{title}' 섹션을 작성하세요. 최소 500단어, 전문 학술 문체."
    return ask_question(question, language)

# ---------------------------
# 그림 생성 및 LaTeX 삽입
# ---------------------------
def generate_figure_image(section_title, topic, figure_number=1, language="ko"):
    os.makedirs("figures", exist_ok=True)
    fig_path = f"figures/{section_title.replace(' ','_')}_fig{figure_number}.png"
    
    # ChatGPT에게 matplotlib 코드 생성 요청
    question = f"'{topic}' 주제 관련 섹션 '{section_title}'용 matplotlib 그래프 코드 생성. 그림 번호 {figure_number}, 캡션 {language}. 코드를 python 실행 가능하게 작성하세요."
    code = ask_question(question, language)
    
    # 안전하게 코드 실행
    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            exec(code, {"plt": plt})
        plt.savefig(fig_path)
        plt.close()
    except Exception as e:
        print(f"[그림 생성 실패] {section_title}: {e}")
        return ""

    # LaTeX figure 환경
    fig_latex = rf"""
\begin{{figure}}[h!]
\centering
\includegraphics[width=0.8\textwidth]{{{fig_path}}}
\caption{{{section_title} 관련 그림 {figure_number}}}
\end{{figure}}
"""
    return fig_latex

# ---------------------------
# 표 생성
# ---------------------------
def generate_table(section_title, topic, table_number=1, language="ko"):
    question = f"'{topic}' 주제 관련 표 LaTeX tabular 코드 생성. 표 번호 {table_number}, 캡션 {language}. python 실행 필요 없음."
    table_code = ask_question(question, language)
    return table_code

# ---------------------------
# BibTeX 생성
# ---------------------------
def generate_bibtex(topic, num_refs=10, language="ko"):
    entries = []
    for i in range(num_refs):
        question = f"'{topic}' 관련 최신 SCI/KCI 논문 1개 BibTeX 생성"
        entry = ask_question(question, language)
        entries.append(entry)
    return entries

# ---------------------------
# 논문 메인 생성
# ---------------------------

def generate_paper(title, topic, language="ko", references=10):
    sections = ["서론", "관련 연구", "연구 방법", "실험 및 결과", "논의", "결론"]

    # LaTeX 문서
    doc = Document(documentclass='article', document_options=['12pt'])
    doc.packages.append(Command('usepackage', 'kotex'))
    doc.packages.append(Command('usepackage', 'setspace'))
    doc.packages.append(Command('usepackage', 'geometry', options='margin=1in'))
    doc.packages.append(Command('usepackage', 'graphicx'))

    doc.preamble.append(Command('title', title))
    doc.preamble.append(Command('author', "자동 생성 논문"))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))
    doc.append(NoEscape(r'\tableofcontents'))
    doc.append(Command('newpage'))

    figure_counter = 1
    table_counter = 1
    generated_files = []

    os.makedirs("figures", exist_ok=True)

    for sec in sections:
        doc.append(NoEscape(f"\\section{{{sec}}}"))
        doc.append(NoEscape(write_section(sec, topic, language)))

        # 그림 삽입
        fig_path = f"figures/{sec.replace(' ','_')}_fig{figure_counter}.png"
        fig_latex = generate_figure_image(sec, topic, figure_counter, language)
        if fig_latex:
            doc.append(NoEscape(fig_latex))
            generated_files.append(fig_path)
            figure_counter += 1

        # 표 삽입
        table_latex = generate_table(sec, topic, table_counter, language)
        if table_latex:
            doc.append(NoEscape(table_latex))
            table_counter += 1

        doc.append(Command('newpage'))

    # BibTeX
    bib_entries = generate_bibtex(topic, references, language)
    bib_file = f"{title}_references.bib"
    with open(bib_file, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(bib_entries))
    generated_files.append(bib_file)

    doc.append(NoEscape(r"\bibliographystyle{apalike}"))
    doc.append(NoEscape(rf"\bibliography{{{title}_references}}"))

    # LaTeX 파일 저장
    os.makedirs("tex", exist_ok=True)
    tex_file = os.path.join("tex", f"{title}.tex")
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(doc.dumps())
    generated_files.append(tex_file)

    return generated_files
