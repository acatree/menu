import sys, os
sys.path.append(os.path.dirname(__file__))  # main.py 기준
from pylatex import Document, Command, NoEscape, Package
import os, re
from . import openai_utils
from . import text_utils
from . import figure_utils
from . import bib_utils

def generate_paper(topic, authors=None, affiliations=None, emails=None, api_key=None):
    """
    전문 학술 논문 스타일 LaTeX 생성
    - scrartcl 기반
    - 저자, 소속, 이메일 포함
    - 표/그래프 전문 스타일 적용
    """

    # 1. 창의적 연구 제목/주제
    creative_title = openai_utils.ask_question(
        f"'{topic}'와 관련되면서 창의적이고 아직 시도되지 않은 연구 논문 제목을 생성하세요. 인용부호 제거",
        api_key=api_key
    ).strip().replace('"', '').replace("'", "")

    research_topic = openai_utils.ask_question(
        f"'{creative_title}'에 해당하는 연구 주제를 1~2문장으로 요약하세요.",
        api_key=api_key
    )

    # 2. LaTeX scrartcl 설정
    doc = Document(documentclass='scrartcl', document_options=['11pt', 'a4paper'])

    # 패키지
    doc.packages.extend([
        Package('geometry', options=['margin=1in']),
        Package('graphicx'),
        Package('amsmath'),
        Package('amssymb'),
        Package('siunitx'),
        Package('hyperref', options='colorlinks=true, linkcolor=blue, citecolor=blue, urlcolor=blue'),
        Package('caption', options='font=small,labelfont=bf'),
        Package('booktabs'),
        Package('setspace'),
        Package('titlesec'),
        Package('float'),
        Package('kotex')
    ])

    # Section/Subsection 스타일
    doc.append(NoEscape(r'\titleformat{\section}{\Large\bfseries}{\thesection}{1em}{}'))
    doc.append(NoEscape(r'\titleformat{\subsection}{\large\bfseries}{\thesubsection}{0.75em}{}'))
    doc.append(NoEscape(r'\titleformat{\subsubsection}{\normalsize\bfseries}{\thesubsubsection}{0.5em}{}'))

    # 줄간격
    doc.append(NoEscape(r'\onehalfspacing'))

    # 3. 제목 / 저자 / 소속 / 이메일
    if authors is None: authors = ["강상규"]
    if affiliations is None: affiliations = ["Department of Physics, Korea University, Seoul, Korea"]
    if emails is None: emails = ["sangkyu@example.com"]

    author_texts = []
    for a, aff, em in zip(authors, affiliations, emails):
        author_texts.append(f"{a}\\thanks{{{aff}. Email: {em}}}")

    doc.preamble.append(NoEscape(r'\title{\Large\bfseries ' + creative_title + '}'))
    doc.preamble.append(NoEscape(r'\author{' + " \\\\ ".join(author_texts) + '}'))
    doc.preamble.append(NoEscape(r'\date{}'))
    doc.append(NoEscape(r'\maketitle'))

    # 4. 초록 / 키워드
    doc.append(NoEscape(r'\begin{abstract}'))
    abstract_text = openai_utils.ask_question(
        f"'{research_topic}'에 대한 논문 초록을 180~220단어로 작성",
        api_key=api_key
    )
    doc.append(NoEscape(text_utils.clean_section_text(abstract_text)))
    doc.append(NoEscape(r'\end{abstract}'))
    doc.append(NoEscape(r'\textbf{키워드:} ' + text_utils.extract_keywords(abstract_text, api_key=api_key)))
    doc.append(Command('newpage'))

    # 5. 참고문헌
    bib_entries = bib_utils.generate_bibtex(research_topic, 10, api_key=api_key)
    with open("references.bib", 'w', encoding='utf-8') as f:
        f.write("\n\n".join(bib_entries))
    bib_keys = [re.search(r'@.*?\{(.*?),', e).group(1) for e in bib_entries if re.search(r'@.*?\{(.*?),', e)]

    # 6. 섹션별 작성
    section_requirements = {
        "서론": 300,
        "관련 연구": 350,
        "연구 방법": 300,
        "분석": 600,
        "결론": 250
    }
    sections = ["서론", "관련 연구", "연구 방법", "분석", "결론"]

    for sec in sections:
        doc.append(NoEscape(f"\\section{{{sec}}}"))
        min_words = section_requirements.get(sec, 300)

        if sec == "분석":
            import pandas as pd, numpy as np
            local_env = {"pd": pd, "np": np}
            df = None

            # 데이터 생성
            data_prompt = (
                f"'{creative_title}' 관련 통계 데이터 예시 생성. pandas DataFrame(df) "
                "5~6개 열, 20~30행 포함."
            )
            data_code = openai_utils.ask_question(data_prompt, api_key=api_key)

            try:
                if "df" not in data_code:
                    data_code = f"import pandas as pd\nimport numpy as np\ndf = {data_code}"
                exec(data_code, local_env)
                df = local_env.get("df", None)
            except Exception:
                df = pd.DataFrame({
                    "변수1": np.random.rand(20),
                    "변수2": np.random.randint(10, 100, 20),
                    "변수3": np.random.normal(0,1,20),
                    "변수4": np.linspace(1,10,20),
                    "변수5": np.random.choice(["A","B","C"],20)
                })

            # 분석 텍스트
            analysis_prompt = (
                f"'{creative_title}' '{sec}' 섹션 작성. df 기반 모델링/통계/해석, 최소 {min_words}단어 이상."
            )
            text_exp = openai_utils.ask_question(analysis_prompt, api_key=api_key)
            text = text_utils.clean_section_text(text_exp)
            doc.append(NoEscape(text))

            # 그래프
            try:
                fig = figure_utils.generate_graph_from_df(sec, df, creative_title)
                if fig:
                    figure_utils.insert_figure(doc, fig, f"{sec} 관련 그래프", placement='H')
            except Exception as e:
                print(f"[그래프 생성 실패: {e}]")

            # 표
            try:
                table_latex = df.to_latex(index=False, longtable=False, caption=f"{sec} 관련 표", label=f"tab:{sec}")
                doc.append(NoEscape(r"\begin{table}[H]\centering" + table_latex + r"\end{table}"))
            except Exception as e:
                print(f"[표 생성 실패: {e}]")

        else:
            # 일반 섹션
            text_exp = openai_utils.ask_question(
                f"'{creative_title}' '{sec}' 섹션 작성, 최소 {min_words}단어 이상.",
                api_key=api_key
            )
            text = text_utils.clean_section_text(text_exp, remove_title=True, section_title=sec)
            text = text_utils.insert_cites(text, bib_keys)
            doc.append(NoEscape(text))

        doc.append(Command('newpage'))

    # 7. 참고문헌
    doc.append(NoEscape(r"\bibliographystyle{apalike}"))
    doc.append(NoEscape(r"\bibliography{references}"))

    # 8. 저장 및 자산 수집
    tex_file = "main.tex"
    doc.generate_tex(tex_file.replace(".tex", ""))

    asset_files = []
    for folder in ["images", "graphs"]:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                asset_files.append(os.path.join(folder, file))

    return tex_file, "references.bib", asset_files, creative_title, research_topic
