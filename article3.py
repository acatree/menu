import os
from pylatex import Document, Command, NoEscape
import openai
import json

openai.api_key = None  # Flask에서 받은 API 키로 runtime에 세팅

# ChatGPT 요청 함수
def ask_question(question):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 한국어 학술 논문 작성 전문가입니다."},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_completion_tokens=2048,
    )
    return response.choices[0].message.content.strip()

# 논문 각 섹션 작성 함수
def write_section(title, topic):
    question = f"'{topic}' 주제에 대해 '{title}' 섹션을 작성하세요. 전문적이고 학술적인 한국어 문체로 작성하세요. 분량은 최소 300단어 이상으로 해주세요."
    return ask_question(question)

# 메인 논문 생성 함수
def generate_paper(title, topic, num_list=3, structure="intro-method-results-discussion", references=10):
    # 논문 구조 정의
    structures = {
        "intro-method-results-discussion": ["서론", "연구 방법", "연구 결과", "논의"],
        "theory-application-conclusion": ["이론적 배경", "적용 사례", "결론"],
        "custom": [f"섹션 {i+1}" for i in range(num_list)]
    }
    section_list = structures.get(structure, structures["intro-method-results-discussion"])

    # 문서 생성 (article 클래스)
    document = Document(documentclass='article', document_options=['12pt'])
    document.packages.append(Command('usepackage', 'kotex'))
    document.packages.append(Command('usepackage', 'setspace'))
    document.packages.append(Command('usepackage', 'geometry', options='margin=1in'))

    # 제목/저자/날짜
    document.preamble.append(Command('title', title))
    document.preamble.append(Command('author', "자동 생성 논문"))
    document.preamble.append(Command('date', NoEscape(r'\today')))
    document.append(NoEscape(r'\maketitle'))
    document.append(NoEscape(r'\tableofcontents'))
    document.append(Command('newpage'))

    # 섹션 작성
    for sec in section_list:
        document.append(NoEscape(f"\\section{{{sec}}}"))
        content = write_section(sec, topic)
        document.append(NoEscape(content))
        document.append(Command('newpage'))

    # 참고문헌 섹션
    document.append(NoEscape(r"\begin{thebibliography}{99}"))
    for i in range(1, references+1):
        ref_question = f"'{topic}'와 관련된 학술 참고문헌 1개를 APA 형식으로 제시하세요."
        ref_text = ask_question(ref_question)
        document.append(NoEscape(f"\\bibitem{{ref{i}}} {ref_text}"))
    document.append(NoEscape(r"\end{thebibliography}"))

    # 저장 (tex만)
    tex_folder = 'tex'
    os.makedirs(tex_folder, exist_ok=True)
    tex_path = os.path.join(tex_folder, f"{title}.tex")

    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(document.dumps())

    return tex_path
