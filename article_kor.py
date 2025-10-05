import os, io, requests, contextlib, re, random, zipfile
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
def clean_section_text(text, remove_title=False, section_title=""):
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = text.replace('**', '')
    if remove_title and section_title:
        text = re.sub(rf'^{section_title}\s*', '', text, flags=re.MULTILINE)
    return text.strip()

# ---------------------------
# 키워드 정리
# ---------------------------
def extract_keywords(text):
    words = re.findall(r'\b[가-힣A-Za-z0-9\-]+\b', text)
    return ', '.join(words[:8])

# ---------------------------
# 안전한 영문 파일명
# ---------------------------
def safe_filename(section_title, suffix):
    mapping = {
        "서론": "intro",
        "관련 연구": "related",
        "연구 방법": "methods",
        "실험 및 결과": "results",
        "논의": "discussion",
        "결론": "conclusion"
    }
    name = mapping.get(section_title, re.sub(r'\W+', '', section_title))
    return f"{name}_{suffix}.png"

# ---------------------------
# DALL·E 이미지 생성
# ---------------------------
def generate_images(api_key, topic, section_title, count=1):
    openai.api_key = api_key
    os.makedirs("images", exist_ok=True)
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
        filename = os.path.join("images", safe_filename(section_title, f"img{i+1}"))
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
    fig_path = os.path.join("graphs", safe_filename(section_title, f"fig{figure_number}"))
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
def insert_figure(doc, file_path, caption_text):
    doc.append(NoEscape(r"\begin{figure}[h]"))
    doc.append(NoEscape(r"\centering"))
    doc.append(NoEscape(f"\includegraphics[width=0.9\\textwidth]{{{file_path}}}"))
    doc.append(NoEscape(f"\caption{{{caption_text}}}"))
    doc.append(NoEscape(r"\end{figure}"))
    doc.append(Command('newpage'))

# ---------------------------
# LaTeX 표 생성
# ---------------------------
def generate_table(section_title, topic, language="ko", api_key=None):
    prompt = (
        f"'{topic}' 주제의 '{section_title}' 섹션 관련 LaTeX tabular 표 생성. "
        "오직 tabular 환경만 출력, 표가 단 두 칸 기준에 맞도록 0.9\\textwidth 조정"
    )
    return ask_question(prompt, language, api_key=api_key)

# ---------------------------
# BibTeX 생성 (완전한 레퍼런스)
# ---------------------------
def generate_bibtex(topic, num_refs=10, language="ko", api_key=None):
    entries = []
    for i in range(num_refs):
        raw_entry = ask_question(
            f"'{topic}' 관련 최신 SCI/KCI 논문 1개 BibTeX 생성, author, title, journal, year, volume, pages 포함",
            language,
            api_key=api_key
        )
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
# 논문 생성 (2단, 단폭 맞춤)
# ---------------------------
def generate_paper(title, topic, api_key=None, language="ko", references=10):
    sections = ["서론", "관련 연구", "연구 방법", "실험 및 결과", "논의", "결론"]
    doc = Document(documentclass='article', document_options=['12pt', 'twocolumn'])
    doc.packages.append(Command('usepackage', 'kotex'))
    doc.packages.append(Command('usepackage', 'geometry', options='a4paper, top=2.5cm, bottom=2.5cm, left=3cm, right=3cm'))
    doc.packages.append(Command('usepackage', 'setspace'))
    doc.packages.append(Command('usepackage', 'graphicx'))
    doc.packages.append(Command('usepackage', 'caption'))
    doc.packages.append(Command('usepackage', 'booktabs'))
    doc.packages.append(Command('usepackage', 'natbib'))

    # 단 간격
    doc.append(NoEscape(r'\setlength{\parskip}{0.5em}'))
    doc.append(NoEscape(r'\setlength{\parindent}{2em}'))

    # 제목/저자
    doc.preamble.append(Command('title', title))
    doc.preamble.append(Command('author', "강상규"))
    # doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))

    # 초록
    doc.append(NoEscape(r'\section*{초록}'))
    abstract_text = clean_section_text(
        ask_question(f"'{topic}' 주제 초록 작성, 150~200단어", language, api_key=api_key)
    )
    doc.append(NoEscape(abstract_text))

    # 키워드
    keywords_text = extract_keywords(ask_question(f"'{topic}' 주제 키워드 8개 생성", language, api_key=api_key))
    doc.append(NoEscape(r'\section*{주제}'))
    doc.append(NoEscape(keywords_text))
    doc.append(Command('newpage'))

    # BibTeX
    bib_entries = generate_bibtex(topic, references, language, api_key=api_key)
    bib_file = "references.bib"
    with open(bib_file, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(bib_entries))
    bib_keys = [re.search(r'@.*?\{(.*?),', e).group(1) for e in bib_entries if re.search(r'@.*?\{(.*?),', e)]

    for sec in sections:
        doc.append(NoEscape(f"\\section{{{sec}}}"))
        section_text = clean_section_text(
            ask_question(f"'{topic}' 주제에 대해 '{sec}' 섹션 작성, 최소 300단어", language, api_key=api_key),
            remove_title=True,
            section_title=sec
        )
        section_text = insert_cites(section_text, bib_keys, prob=0.2)
        doc.append(NoEscape(section_text))

        # 실험 및 분석 섹션 그래프 필수
        if sec in ["실험 및 결과", "연구 방법"]:
            graph_path = generate_graph(sec, topic, figure_number=1, language=language, api_key=api_key)
            if graph_path:
                insert_figure(doc, graph_path, f"{sec} 관련 그래프")

        # 표
        table_code = generate_table(sec, topic, language=language, api_key=api_key)
        if table_code:
            doc.append(NoEscape(r"\begin{table}[h]"))
            doc.append(NoEscape(r"\centering"))
            doc.append(NoEscape(r"\resizebox{0.9\textwidth}{!}{"))
            doc.append(NoEscape(table_code))
            doc.append(NoEscape("}"))
            doc.append(NoEscape(f"\\caption{{{sec} 관련 표}}"))
            doc.append(NoEscape(r"\end{table}"))

        # 이미지
        image_files = generate_images(api_key, topic, sec, count=1)
        for img_file in image_files:
            insert_figure(doc, img_file, f"{sec} 관련 이미지")

        doc.append(Command('newpage'))

    doc.append(NoEscape(r"\bibliographystyle{apalike}"))
    doc.append(NoEscape(r"\bibliography{references}"))

    # LaTeX 저장
    tex_file = f"{title}.tex"
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(doc.dumps())

    # ZIP 생성
    zip_file = f"{title}_files.zip"
    with zipfile.ZipFile(zip_file, 'w') as zipf:
        zipf.write(tex_file)
        zipf.write(bib_file)
        for folder in ["images", "graphs"]:
            if os.path.exists(folder):
                for file in os.listdir(folder):
                    zipf.write(os.path.join(folder, file))
    return tex_file, bib_file, zip_file
    
