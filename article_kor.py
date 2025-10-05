import os, io, requests, contextlib, re, random
from pylatex import Document, Command, NoEscape
import matplotlib.pyplot as plt
import openai

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
# 텍스트 클린업
# ---------------------------
def clean_section_text(text):
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # #, ##, ### 제거
    text = text.replace('**', '')  # 강조 제거
    return text

# ---------------------------
# 키워드 정리
# ---------------------------
def extract_keywords(text):
    keywords = re.findall(r'\b[\w\-]+\b', text)
    return ', '.join(keywords[:5])

# ---------------------------
# DALL·E 이미지 생성
# ---------------------------
def generate_images(api_key, topic, section_title, count=1):
    openai.api_key = api_key
    image_files = []

    for i in range(count):
        prompt = (
            f"'{topic}' 주제의 '{section_title}' 섹션에 적합한 학술용 시각 자료 생성. "
            "논문에 들어갈 수 있는 형태의 데이터 시각화, 그래프, 구조 다이어그램, 실험 결과 시각화 등. "
            "직접적인 인물 이름이나 브랜드는 제외. "
            "깔끔하고 전문적인 스타일, 발표/논문용 그림 느낌. 흑백그림, 스케치 등"
        )
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
        filename = f"{section_title.replace(' ','_')}_img{i+1}.png"
        with open(filename, 'wb') as f:
            f.write(img_data)
        image_files.append(filename)
    return image_files

# ---------------------------
# Matplotlib 그래프 생성
# ---------------------------
def generate_graph(section_title, topic, figure_number=1, language="ko", api_key=None):
    openai.api_key = api_key
    fig_path = f"{section_title.replace(' ','_')}_fig{figure_number}.png"

    question = (
        f"'{topic}' 주제 관련 '{section_title}' 섹션용 matplotlib 그래프 코드 생성. "
        f"그림 번호 {figure_number}, 캡션 {language}. "
        "python 실행 가능한 완전한 코드로 출력, plt.savefig('{fig_path}') 포함"
    )
    code = ask_question(question, language, api_key=api_key)

    try:
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
def insert_figure(doc, file_name, caption_text):
    doc.append(NoEscape(r"\begin{figure}[h]"))
    doc.append(NoEscape(r"\centering"))
    doc.append(NoEscape(f"\includegraphics[width=0.8\\textwidth]{{{file_name}}}"))
    doc.append(NoEscape(f"\caption{{{caption_text}}}"))
    doc.append(NoEscape(r"\end{figure}"))
    doc.append(Command('newpage'))

# ---------------------------
# LaTeX 표 생성
# ---------------------------
def generate_table(section_title, topic, language="ko", api_key=None):
    prompt = (
        f"'{topic}' 주제의 '{section_title}' 섹션 관련 LaTeX tabular 표 생성. "
        "오직 tabular 환경만 출력"
    )
    return ask_question(prompt, language, api_key=api_key)

# ---------------------------
# BibTeX 생성 및 정제
# ---------------------------
def generate_bibtex(topic, num_refs=10, language="ko", api_key=None):
    entries = []
    for i in range(num_refs):
        raw_entry = ask_question(f"'{topic}' 관련 최신 SCI/KCI 논문 1개 BibTeX 생성", language, api_key=api_key)
        # @article{...} 블록만 추출
        match = re.search(r'(@\w+\{[^}]+\})', raw_entry, flags=re.DOTALL)
        if match:
            entries.append(match.group(1))
    return entries

# ---------------------------
# 본문에 랜덤 cite 삽입
# ---------------------------
def insert_cites(text, bib_keys, prob=0.2):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for i, s in enumerate(sentences):
        if bib_keys and random.random() < prob:
            key = random.choice(bib_keys)
            sentences[i] = s + f" \\cite{{{key}}}"
    return ' '.join(sentences)

# ---------------------------
# KCI 스타일 논문 생성 (랜덤 그림/표/그래프)
# ---------------------------
def generate_paper(title, topic, api_key=None, language="ko", references=10,
                   graph_prob=0.5, image_prob=0.3, table_prob=0.2):
    sections = ["서론", "관련 연구", "연구 방법", "실험 및 결과", "논의", "결론"]

    doc = Document(documentclass='article', document_options=['12pt'])
    doc.packages.append(Command('usepackage', 'kotex'))
    doc.packages.append(Command('usepackage', 'geometry', options='a4paper, top=2.5cm, bottom=2.5cm, left=3cm, right=3cm'))
    doc.packages.append(Command('usepackage', 'setspace'))
    doc.packages.append(Command('usepackage', 'graphicx'))
    doc.packages.append(Command('usepackage', 'caption'))
    doc.packages.append(Command('usepackage', 'booktabs'))
    doc.packages.append(Command('usepackage', 'natbib'))

    # 제목/저자
    doc.preamble.append(Command('title', title))
    doc.preamble.append(Command('author', "강상규"))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))

    # 초록
    doc.append(NoEscape(r'\begin{abstract}'))
    abstract_text = clean_section_text(ask_question(f"'{topic}' 주제 초록(Abstract) 작성, 150~200단어", language, api_key=api_key))
    doc.append(NoEscape(abstract_text))
    doc.append(NoEscape(r'\end{abstract}'))

    # 키워드
    keywords_text = extract_keywords(ask_question(f"'{topic}' 주제 키워드 5개 생성", language, api_key=api_key))
    doc.append(NoEscape(r'\textbf{Keywords}: ' + keywords_text))
    doc.append(Command('newpage'))

    # BibTeX
    bib_entries = generate_bibtex(topic, references, language, api_key=api_key)
    bib_file = "references.bib"
    with open(bib_file, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(bib_entries))

    # Bib 키 목록
    bib_keys = []
    for entry in bib_entries:
        m = re.search(r'@.*?\{(.*?),', entry)
        if m:
            bib_keys.append(m.group(1))

    for sec in sections:
        doc.append(NoEscape(f"\\section{{{sec}}}"))
        section_text = clean_section_text(ask_question(f"'{topic}' 주제에 대해 '{sec}' 섹션 작성, 최소 300단어", language, api_key=api_key))
        # 랜덤 cite 삽입
        section_text = insert_cites(section_text, bib_keys, prob=0.2)
        doc.append(NoEscape(section_text))

        # 랜덤 그래프
        if random.random() < graph_prob:
            graph_path = generate_graph(sec, topic, figure_number=1, language=language, api_key=api_key)
            if graph_path:
                insert_figure(doc, graph_path, f"{sec} 관련 그래프")

        # 랜덤 이미지
        if random.random() < image_prob:
            image_files = generate_images(api_key, topic, sec, count=1)
            for img_file in image_files:
                insert_figure(doc, img_file, f"{sec} 관련 이미지")

        # 랜덤 표
        if random.random() < table_prob:
            table_code = generate_table(sec, topic, language=language, api_key=api_key)
            if table_code:
                doc.append(NoEscape(r"\begin{table}[h]"))
                doc.append(NoEscape(r"\centering"))
                doc.append(NoEscape(table_code))
                doc.append(NoEscape(f"\\caption{{{sec} 관련 표}}"))
                doc.append(NoEscape(r"\end{table}"))

        doc.append(Command('newpage'))

    doc.append(NoEscape(r"\bibliographystyle{apalike}"))
    doc.append(NoEscape(r"\bibliography{references}"))

    # LaTeX 저장
    tex_file = f"{title}.tex"
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(doc.dumps())

    return [tex_file, bib_file]
