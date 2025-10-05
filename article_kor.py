import os
import io
import requests
import contextlib
import matplotlib.pyplot as plt
import openai
from openai import OpenAI
from pylatex import Document, Command, NoEscape

openai.api_key = None  # Flask 또는 환경 변수에서 설정

# ---------------------------
# ChatGPT 질의 함수
# ---------------------------
def 질문_요청(질문, 언어="ko"):
    시스템_프롬프트 = "당신은 SCI/KCI 수준의 한국어 학술 논문 작성 전문가입니다."
    응답 = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": 시스템_프롬프트},
            {"role": "user", "content": 질문}
        ],
        temperature=0.7,
        max_completion_tokens=3000,
    )
    return 응답.choices[0].message.content.strip()


# ---------------------------
# 시각 이미지 생성 (DALL·E)
# ---------------------------
def 이미지_생성(api_key, 주제, 섹션제목, 개수=1):
    클라이언트 = OpenAI(api_key=api_key)
    os.makedirs("이미지", exist_ok=True)
    생성된_이미지 = []

    for i in range(개수):
        프롬프트 = (
            f"'{주제}' 주제의 '{섹션제목}' 섹션을 시각적으로 표현한 장면. "
            f"인물 이름이나 브랜드 없이 묘사적, 추상적 스타일. "
            f"변형 {i+1}"
        )
        응답 = 클라이언트.images.generate(
            model="dall-e-3",
            prompt=프롬프트,
            size="1024x1024"
        )

        이미지_URL = 응답.data[0].url if 응답.data and 응답.data[0].url else None
        if not 이미지_URL:
            raise ValueError("❌ 이미지 URL을 생성하지 못했습니다.")
        데이터 = requests.get(이미지_URL).content

        파일이름 = f"이미지/{섹션제목.replace(' ', '_')}_이미지{i+1}.png"
        with open(파일이름, 'wb') as f:
            f.write(데이터)
        생성된_이미지.append(파일이름)

    return 생성된_이미지


# ---------------------------
# 그래프 생성 (Matplotlib)
# ---------------------------
def 그래프_생성(섹션제목, 주제, 그림번호=1):
    os.makedirs("그래프", exist_ok=True)
    파일경로 = f"그래프/{섹션제목.replace(' ', '_')}_그림{그림번호}.png"

    질문 = (
        f"'{주제}' 주제의 '{섹션제목}' 섹션을 설명하는 matplotlib 그래프 코드 생성. "
        f"그림 번호는 {그림번호}이며, 캡션은 한국어로 작성하세요. "
        f"파이썬에서 바로 실행 가능한 완전한 코드로 작성."
    )
    코드 = 질문_요청(질문, "ko")

    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            exec(코드, {"plt": plt})
        plt.savefig(파일경로)
        plt.close()
    except Exception as e:
        print(f"[⚠ 그래프 생성 실패] {섹션제목}: {e}")
        return ""

    return 파일경로


# ---------------------------
# 표 생성 (LaTeX)
# ---------------------------
def 표_생성(섹션제목, 주제, 표번호=1):
    질문 = f"'{주제}' 주제의 '{섹션제목}' 섹션과 관련된 표 LaTeX tabular 코드 생성. 표 번호는 {표번호}, 캡션은 한국어로 작성."
    표코드 = 질문_요청(질문, "ko")
    return 표코드


# ---------------------------
# 참고문헌 (BibTeX)
# ---------------------------
def 참고문헌_생성(주제, 논문수=10):
    항목들 = []
    for i in range(논문수):
        질문 = f"'{주제}'와 관련된 최근 한국어 SCI/KCI 논문 1개의 BibTeX 항목을 생성하세요."
        항목 = 질문_요청(질문, "ko")
        항목들.append(항목)
    return 항목들


# ---------------------------
# 논문 전체 생성
# ---------------------------
def 논문_생성(제목, 주제, api_key=None, 참고문헌수=10):
    섹션목록 = ["서론", "관련 연구", "연구 방법", "실험 및 결과", "논의", "결론"]

    문서 = Document(documentclass='article', document_options=['12pt'])
    문서.packages.append(Command('usepackage', 'kotex'))
    문서.packages.append(Command('usepackage', 'setspace'))
    문서.packages.append(Command('usepackage', 'geometry', options='margin=1in'))
    문서.packages.append(Command('usepackage', 'graphicx'))

    문서.preamble.append(Command('title', 제목))
    문서.preamble.append(Command('author', "강상규"))
    문서.preamble.append(Command('date', NoEscape(r'\today')))
    문서.append(NoEscape(r'\maketitle'))
    문서.append(NoEscape(r'\tableofcontents'))
    문서.append(Command('newpage'))

    그림번호 = 1
    표번호 = 1
    생성된_파일목록 = []

    for 섹션 in 섹션목록:
        문서.append(NoEscape(f"\\section{{{섹션}}}"))
        본문 = 질문_요청(f"'{주제}' 주제의 '{섹션}' 섹션을 300단어 이상, 전문적인 학술 문체로 작성하세요.", "ko")
        문서.append(NoEscape(본문))

        # --------------------------
        # 주석으로 그림 생성 순서 명시
        # --------------------------
        문서.append(NoEscape(f"% 그림 {그림번호}: 그래프 생성 코드"))
        그래프파일 = 그래프_생성(섹션, 주제, 그림번호)
        if 그래프파일:
            생성된_파일목록.append(그래프파일)
        그림번호 += 1

        문서.append(NoEscape(f"% 그림 {그림번호}: DALL·E 시각 이미지"))
        이미지파일 = 이미지_생성(api_key, 주제, 섹션, 개수=1)
        생성된_파일목록.extend(이미지파일)
        그림번호 += 1
        # --------------------------

        # 표 생성
        표코드 = 표_생성(섹션, 주제, 표번호)
        if 표코드:
            문서.append(NoEscape(표코드))
            표번호 += 1

        문서.append(Command('newpage'))

    # ---------------------------
    # 참고문헌 삽입
    # ---------------------------
    참고목록 = 참고문헌_생성(주제, 참고문헌수)
    bib파일 = f"{제목}_참고문헌.bib"
    with open(bib파일, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(참고목록))
    생성된_파일목록.append(bib파일)

    문서.append(NoEscape(r"\bibliographystyle{apalike}"))
    문서.append(NoEscape(rf"\bibliography{{{제목}_참고문헌}}"))

    # ---------------------------
    # LaTeX 파일 저장
    # ---------------------------
    os.makedirs("tex", exist_ok=True)
    tex파일 = os.path.join("tex", f"{제목}.tex")
    with open(tex파일, 'w', encoding='utf-8') as f:
        f.write(문서.dumps())
    생성된_파일목록.append(tex파일)

    return 생성된_파일목록
