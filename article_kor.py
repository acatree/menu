import os, io, requests, contextlib
from pylatex import Document, Command, NoEscape
import matplotlib.pyplot as plt
import openai

openai.api_key = None  # Flask 또는 환경변수에서 세팅

def ask_question(question, language="ko", api_key=None):
    if api_key:
        openai.api_key = api_key
    system_prompt = "당신은 SCI/KCI 수준 학술 논문 작성 전문가입니다." if language == "ko" else "You are an expert in academic paper writing."
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
        # 이미지 생성 시 재시도 루프
        for attempt in range(3):
            response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024"
            )
            image_url = response.data[0].url if response.data and response.data[0].url else None
            if image_url:
                break
        if not image_url:
            print(f"[이미지 생성 실패] {section_title}")
            continue
        img_data = requests.get(image_url).content
        filename = f"images/{section_title.replace(' ','_')}_img{i+1}.png"
        with open(filename, 'wb') as f:
            f.write(img_data)
        image_files.append(filename)
    return image_files

# ---------------------------
# Matplotlib 그래프 생성
# ---------------------------
def generate_graph(section_title, topic, figure_number=1, language="ko", api_key=None):
    openai.api_key = api_key
    os.makedirs("graphs", exist_ok=True)
    fig_path = f"graphs/{section_title.replace(' ','_')}_fig{figure_number}.png"

    question = (
        f"'{topic}' 주제 관련 '{section_title}' 섹션용 matplotlib 그래프 코드 생성. "
        f"그림 번호 {figure_number}, 캡션 {language}. "
        "python 실행 가능한 완전한 코드로 출력, plt.savefig('{fig_path}') 포함"
    )
    code = ask_question(question, language, api_key=api_key)

    try:
        # exec에서 plt 객체 전달
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            exec(code, {"plt": plt})
        plt.close()
    except Exception as e:
        print(f"[그래프 생성 실패] {section_title}: {e}")
        return ""
    return fig_path

# ---------------------------
# Figure 삽입
# ---------------------------
def insert_figure(doc, file_path, figure_counter, caption_text):
    doc.append(NoEscape(r"\begin{figure}[h]"))
    doc.append(NoEscape(r"\centering"))
    doc.append(NoEscape(f"\includegraphics[width=0.8\\textwidth]{{{file_path}}}"))
    doc.append(NoEscape(f"\caption{{Figure {figure_counter}: {caption_text}}}"))
    doc.append(NoEscape(r"\end{figure}"))
    doc.append(Command('newpage'))
    return figure_counter + 1

# ---------------------------
# LaTeX 표 생성
# ---------------------------
def generate_table(section_title, topic, table_number=1, language="ko", api_key=None):
    prompt = (
        f"'{topic}' 주제의 '{section_title}' 섹션 관련 LaTeX tabular 표 생성. "
        f"표 번호 {table_number}, 캡션 {language}. "
        "오직 tabular 환경만 출력"
    )
    return ask_question(prompt, language, api_key=api_key)

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
# KCI 스타일 논문 전체 생성
# ---------------------------
def generate_paper(title, topic, api_key=None, language="ko", references=10):
    sections = ["서론", "관련 연구", "연구 방법", "실험 및 결과", "논의", "결론"]

    # KCI.cls 적용
    doc = Document(documentclass='kci', document_options=['12pt'])
    doc.packages.append(Command('usepackage', 'kotex'))
    doc.packages.append(Command('usepackage', 'graphicx'))
    doc.packages.append(Command('usepackage', 'caption'))
    doc.packages.append(Command('usepackage', 'setspace'))

    # 제목/저자
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
        section_text = ask_question(f"'{topic}' 주제에 대해 '{sec}' 섹션 작성, 최소 300단어", language, api_key=api_key)
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

        # 표 삽입
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
