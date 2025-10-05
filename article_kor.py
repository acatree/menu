import os, io, requests
from pylatex import Document, Command, NoEscape
import openai
import matplotlib.pyplot as plt
import contextlib
from openai import OpenAI

openai.api_key = None  # Flask 또는 환경변수에서 세팅
# ---------------------------
# ChatGPT 요청 함수
# ---------------------------
def ask_question(question, language="ko", api_key=None):
    if api_key:
        openai.api_key = api_key
    system_prompt = "당신은 SCI/KCI 수준 학술 논문 작성 전문가입니다." if language=="ko" else "You are an expert in academic paper writing."
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_completion_tokens=3000
    )
    return response.choices[0].message.content.strip()

# ---------------------------
# DALL·E 이미지 생성
# ---------------------------
def generate_images(api_key, topic, section_title, count=1):
    openai.api_key = api_key
    os.makedirs("images", exist_ok=True)
    image_files = []

    for i in range(count):
        prompt = (
            f"'{topic}' 주제의 '{section_title}' 섹션을 시각적으로 표현한 장면. "
            "직접적인 인물 이름이나 브랜드 없이 묘사적, 추상적 스타일."
        )
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024"
        )
        image_url = response.data[0].url if response.data and response.data[0].url else None
        if not image_url:
            raise ValueError("❌ 이미지 URL 생성 실패")
        img_data = requests.get(image_url).content
        filename = f"images/{section_title.replace(' ','_')}_img{i+1}.png"
        with open(filename, 'wb') as f:
            f.write(img_data)
        image_files.append(filename)
    return image_files

# ---------------------------
# 그래프 생성 (Matplotlib)
# ---------------------------
def generate_graph(section_title, topic, figure_number=1, language="ko", api_key=None):
    openai.api_key = api_key
    os.makedirs("graphs", exist_ok=True)
    fig_path = f"graphs/{section_title.replace(' ','_')}_fig{figure_number}.png"

    question = (
        f"'{topic}' 주제 관련 '{section_title}' 섹션용 matplotlib 그래프 코드 생성. "
        f"그림 번호 {figure_number}, 캡션 {language}. "
        "python에서 실행 가능한 완전한 코드로 출력"
    )
    code = ask_question(question, language, api_key=api_key)

    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            exec(code, {"plt": plt})
        plt.savefig(fig_path)
        plt.close()
    except Exception as e:
        print(f"[그래프 생성 실패] {section_title}: {e}")
        return ""
    return fig_path

# ---------------------------
# 테이블 생성
# ---------------------------
def generate_table(section_title, topic, table_number=1, language="ko", api_key=None):
    table_code = ask_question(
        f"'{topic}' 주제 관련 LaTeX tabular 코드 생성. "
        f"표 번호 {table_number}, 캡션 {language}. "
        "⚠ tabular 환경만, \\documentclass, \\begin{{document}}, \\end{{document}} 포함하지 말 것.",
        language,
        api_key=api_key
    )
    return table_code

# ---------------------------
# BibTeX 생성
# ---------------------------
def generate_bibtex(topic, num_refs=10, language="ko", api_key=None):
    entries = []
    for i in range(num_refs):
        entry = ask_question(f"'{topic}' 관련 최신 SCI/KCI 논문 1개 BibTeX 생성", language, api_key=api_key)
        entries.append(entry)
    return entries

# ---------------------------
# Figure 삽입 함수 (그래프 + 이미지)
# ---------------------------
def insert_figure(doc, file_path, figure_counter, caption_text):
    """
    doc: pylatex Document
    file_path: 삽입할 이미지/그래프 경로
    figure_counter: 현재 figure 번호 (int)
    caption_text: 캡션 내용 (str)
    """
    doc.append(NoEscape(r"\begin{figure}[h]"))
    doc.append(NoEscape(r"\centering"))
    doc.append(NoEscape(f"\\includegraphics[width=0.8\\textwidth]{{{file_path}}}"))
    doc.append(NoEscape(f"\\caption{{Figure {figure_counter}: {caption_text}}}"))
    doc.append(NoEscape(r"\end{figure}"))
    doc.append(Command('newpage'))  # 필요시 페이지 구분
    return figure_counter + 1  # 다음 번호 반환

# ---------------------------
# KCI 스타일 논문 생성
# ---------------------------
def generate_paper(title, topic, api_key=None, language="ko", references=10):
    sections = ["서론", "관련 연구", "연구 방법", "실험 및 결과", "논의", "결론"]

    # KCI.cls 사용
    doc = Document(documentclass='kci', document_options=['12pt'])
    doc.packages.append(Command('usepackage', 'kotex'))
    doc.packages.append(Command('usepackage', 'graphicx'))
    doc.packages.append(Command('usepackage', 'caption'))
    doc.packages.append(Command('usepackage', 'setspace'))

    # 제목/저자/초록/키워드
    doc.preamble.append(Command('title', title))
    doc.preamble.append(Command('author', "강상규"))
    doc.append(NoEscape(r'\maketitle'))

    # 초록(Abstract)
    doc.append(NoEscape(r'\begin{abstract}'))
    abstract_text = ask_question(f"'{topic}' 주제 초록(Abstract) 작성, 150~200단어", language, api_key=api_key)
    doc.append(NoEscape(abstract_text))
    doc.append(NoEscape(r'\end{abstract}'))

    # 키워드
    keywords_text = ask_question(f"'{topic}' 주제 키워드 5개 생성", language, api_key=api_key)
    doc.append(NoEscape(r'\textbf{Keywords}: ' + keywords_text))
    doc.append(Command('newpage'))

    figure_counter = 1
    table_counter = 1
    generated_files = []

    for sec in sections:
        doc.append(NoEscape(f"\\section{{{sec}}}"))

        # 섹션 본문
        section_text = ask_question(f"'{topic}' 주제에 대해 '{sec}' 섹션을 작성하세요. 최소 300단어.", language, api_key=api_key)
        doc.append(NoEscape(section_text))

        # 그래프 삽입
        graph_path = generate_graph(sec, topic, figure_counter, language, api_key=api_key)
        if graph_path:
            figure_counter = insert_figure(doc, graph_path, figure_counter, f"{sec} 관련 그래프")
            generated_files.append(graph_path)

        # DALL·E 이미지 삽입
        image_files = generate_images(api_key, topic, sec, count=1)
        for img_file in image_files:
            figure_counter = insert_figure(doc, img_file, figure_counter, f"{sec} 관련 이미지")
            generated_files.append(img_file)

        # 테이블 삽입
        table_code = generate_table(sec, topic, table_counter, language, api_key=api_key)
        if table_code:
            doc.append(NoEscape(r"\begin{table}[h]"))
            doc.append(NoEscape(r"\centering"))
            doc.append(NoEscape(table_code))
            doc.append(NoEscape(f"\\caption{{{sec} 관련 표}}"))
            doc.append(NoEscape(r"\end{table}"))
            table_counter += 1

        doc.append(Command('newpage'))

    # BibTeX
    bib_entries = generate_bibtex(topic, references, language, api_key=api_key)
    bib_file = f"{title}_references.bib"
    with open(bib_file, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(bib_entries))
    generated_files.append(bib_file)

    doc.append(NoEscape(r"\bibliographystyle{kci}"))
    doc.append(NoEscape(rf"\bibliography{{{title}_references}}"))

    # LaTeX 저장
    os.makedirs("tex", exist_ok=True)
    tex_file = os.path.join("tex", f"{title}.tex")
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(doc.dumps())
    generated_files.append(tex_file)

    return generated_files



# ---------------------------
# ChatGPT 요청 함수
# ---------------------------
def ask_question(question, language="ko", api_key=None):
    if api_key:
        openai.api_key = api_key  # Flask에서 받은 API 키 반영
    system_prompt = "당신은 SCI/KCI 수준 학술 논문 작성 전문가입니다." if language == "ko" else "You are an expert in academic paper writing."
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
# 시각 이미지 생성 (DALL·E)
# ---------------------------
def generate_images(api_key, topic, section_title, count=1):
    openai.api_key = api_key
    os.makedirs("images", exist_ok=True)
    image_files = []

    for i in range(count):
        prompt = (
            f"'{topic}' 주제의 '{section_title}' 섹션을 시각적으로 표현한 장면. "
            f"직접적인 인물 이름이나 브랜드 없이 묘사적, 추상적 스타일. "
            f"variation {i+1}"
        )
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024"
        )

        image_url = response.data[0].url if response.data and response.data[0].url else None
        if not image_url:
            raise ValueError("❌ 이미지 URL을 생성하지 못했습니다.")
        img_data = requests.get(image_url).content

        filename = f"images/{section_title.replace(' ', '_')}_img{i+1}.png"
        with open(filename, 'wb') as f:
            f.write(img_data)
        image_files.append(filename)
    return image_files
# ---------------------------
# 그래프 생성 (Matplotlib)
# ---------------------------
def generate_graph(section_title, topic, figure_number=1, language="ko", api_key=None):
    openai.api_key = api_key
    os.makedirs("graphs", exist_ok=True)
    fig_path = f"graphs/{section_title.replace(' ','_')}_fig{figure_number}.png"

    question = (
        f"'{topic}' 주제 관련 '{section_title}' 섹션용 matplotlib 그래프 코드 생성. "
        f"그림 번호 {figure_number}, 캡션 {language}. "
        f"python 실행 가능한 완전한 코드로."
    )
    code = ask_question(question, language, api_key=api_key)

    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            exec(code, {"plt": plt})
        plt.savefig(fig_path)
        plt.close()
    except Exception as e:
        print(f"[그래프 생성 실패] {section_title}: {e}")
        return ""

    return fig_path
# ---------------------------
# 표 생성
# ---------------------------
def generate_table(section_title, topic, table_number=1, language="ko", api_key=None):
    table_code = ask_question(f"'{topic}' 주제 관련 표 LaTeX tabular 코드 생성. 표 번호 {table_number}, 캡션 {language}.", language, api_key=api_key)
    return table_code

# ---------------------------
# BibTeX 생성
# ---------------------------
def generate_bibtex(topic, num_refs=10, language="ko", api_key=None):
    entries = []
    for i in range(num_refs):
        entry = ask_question(f"'{topic}' 관련 최신 SCI/KCI 논문 1개 BibTeX 생성", language, api_key=api_key)
        entries.append(entry)
    return entries

# ---------------------------
# 논문 전체 생성
# ---------------------------
def generate_paper(title, topic, api_key=None, language="ko", references=10):
    sections = ["서론", "관련 연구", "연구 방법", "실험 및 결과", "논의", "결론"]

    doc = Document(documentclass='article', document_options=['12pt'])
    doc.packages.append(Command('usepackage', 'kotex'))
    doc.packages.append(Command('usepackage', 'setspace'))
    doc.packages.append(Command('usepackage', 'geometry', options='margin=1in'))
    doc.packages.append(Command('usepackage', 'graphicx'))

    doc.preamble.append(Command('title', title))
    doc.preamble.append(Command('author', "강상규"))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))
    doc.append(NoEscape(r'\tableofcontents'))
    doc.append(Command('newpage'))

    figure_counter = 1
    table_counter = 1
    generated_files = []

    for sec in sections:
        doc.append(NoEscape(f"\\section{{{sec}}}"))
        section_text = ask_question(f"'{topic}' 주제에 대해 '{sec}' 섹션을 작성하세요. 최소 300단어.", language, api_key=api_key)
        doc.append(NoEscape(section_text))

        doc.append(NoEscape(f"% Figure {figure_counter}: 그래프 생성 코드"))
        graph_path = generate_graph(sec, topic, figure_counter, language, api_key=api_key)
        if graph_path:
            generated_files.append(graph_path)
        figure_counter += 1

        doc.append(NoEscape(f"% Figure {figure_counter}: 시각 이미지 (DALL·E)"))
        image_files = generate_images(api_key, topic, sec, count=1)
        generated_files.extend(image_files)
        figure_counter += 1

        table_code = generate_table(sec, topic, table_counter, language, api_key=api_key)
        if table_code:
            doc.append(NoEscape(table_code))
            table_counter += 1

        doc.append(Command('newpage'))

    bib_entries = generate_bibtex(topic, references, language, api_key=api_key)
    bib_file = f"{title}_references.bib"
    with open(bib_file, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(bib_entries))
    generated_files.append(bib_file)

    doc.append(NoEscape(r"\bibliographystyle{apalike}"))
    doc.append(NoEscape(rf"\bibliography{{{title}_references}}"))

    os.makedirs("tex", exist_ok=True)
    tex_file = os.path.join("tex", f"{title}.tex")
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(doc.dumps())
    generated_files.append(tex_file)

    return generated_files
