import sys, os
sys.path.append(os.path.dirname(__file__))  # main.py 기준
from pylatex import Document, Command, NoEscape, Package
import os, re
from . import openai_utils
from . import text_utils
from . import figure_utils
from . import bib_utils

def generate_paper(topic, api_key=None):
    # 1. 창의적 연구 제목/주제
    creative_title = openai_utils.ask_question(
        f"'{topic}'와 관련되면서 창의적이고 아직 시도되지 않은 연구 논문 제목을 "
        "하나 생성해 주세요. 인용부호는 제거하세요.",
        api_key=api_key
    ).strip().replace('"', '').replace("'", "")

    research_topic = openai_utils.ask_question(
        f"'{creative_title}'에 해당하는 연구 주제를 1~2문장으로 요약해 주세요.",
        api_key=api_key
    )

    # 2. LaTeX scrartcl 설정
    doc = Document(documentclass='scrartcl', document_options=['11pt', 'a4paper'])
    # 패키지
    doc.packages.append(Package('geometry', options=['margin=1in']))
    doc.packages.append(Package('graphicx'))
    doc.packages.append(Package('amsmath'))
    doc.packages.append(Package('amssymb'))
    doc.packages.append(Package('siunitx'))
    doc.packages.append(Package('hyperref'))
    doc.packages.append(Package('caption'))
    doc.packages.append(Package('booktabs'))
    doc.packages.append(Package('setspace'))
    doc.packages.append(Package('titlesec'))
    doc.packages.append(Package('kotex'))

    # 줄간격
    doc.append(NoEscape(r'\onehalfspacing'))
    # 제목 스타일
    doc.preamble.append(NoEscape(r'\title{\Large\bfseries ' + creative_title + '}'))
    doc.preamble.append(NoEscape(r'\author{강상규}'))
    doc.preamble.append(NoEscape(r'\date{}'))  # 날짜 공란
    doc.append(NoEscape(r'\maketitle'))

    # 3. 초록/키워드
    doc.append(NoEscape(r'\begin{abstract}'))
    abstract_text = openai_utils.ask_question(
        f"'{research_topic}'에 대한 논문 초록을 180~220단어로 작성",
        api_key=api_key
    )
    doc.append(NoEscape(text_utils.clean_section_text(abstract_text)))
    doc.append(NoEscape(r'\end{abstract}'))

    doc.append(NoEscape(r'\textbf{키워드:} ' + text_utils.extract_keywords(abstract_text, api_key=api_key)))
    doc.append(Command('newpage'))

    # 4. 참고문헌 생성
    bib_entries = bib_utils.generate_bibtex(research_topic, 10, api_key=api_key)
    with open("references.bib", 'w', encoding='utf-8') as f:
        f.write("\n\n".join(bib_entries))
    bib_keys = [re.search(r'@.*?\{(.*?),', e).group(1) for e in bib_entries if re.search(r'@.*?\{(.*?),', e)]

    # 5. 섹션별 작성
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
                f"'{creative_title}' 주제와 관련된 통계 데이터 예시를 생성하세요. "
                "pandas DataFrame 형식으로, 반드시 변수명 'df'를 사용하고 "
                "5~6개 열(column), 20~30개 행(row)을 포함하도록 하세요."
            )
            data_code = openai_utils.ask_question(data_prompt, api_key=api_key)

            try:
                if "df" not in data_code:
                    data_code = f"import pandas as pd\nimport numpy as np\ndf = {data_code}"
                exec(data_code, local_env)
                df = local_env.get("df", None)
            except Exception as e:
                print(f"[데이터 생성 실패: {e}] 대체 데이터 사용")
                df = pd.DataFrame({
                    "변수1": np.random.rand(20),
                    "변수2": np.random.randint(10, 100, 20),
                    "변수3": np.random.normal(0, 1, 20),
                    "변수4": np.linspace(1, 10, 20),
                    "변수5": np.random.choice(["A", "B", "C"], 20)
                })

            # 분석 텍스트
            analysis_prompt = (
                f"'{creative_title}'의 '{sec}' 섹션을 작성하세요. "
                "df 데이터를 기반으로 한 수학적 모델링, 통계 분석, 결과 해석 포함, "
                f"최소 {min_words}단어 이상."
            )
            text_exp = openai_utils.ask_question(analysis_prompt, api_key=api_key)
            text = text_utils.clean_section_text(text_exp)
            doc.append(NoEscape(text))

            # 그래프
            try:
                fig = figure_utils.generate_graph_from_df(sec, df, creative_title)
                if fig:
                    figure_utils.insert_figure(doc, fig, f"{sec} 관련 그래프")
            except Exception as e:
                print(f"[그래프 생성 실패: {e}]")

            # 표
            try:
                table_latex = df.to_latex(index=False)
                doc.append(NoEscape(r"\begin{table}[h]"))
                doc.append(NoEscape(r"\centering"))
                doc.append(NoEscape(r"\resizebox{0.9\textwidth}{!}{" + table_latex + "}"))
                doc.append(NoEscape(f"\\caption{{{sec} 관련 표}}"))
                doc.append(NoEscape(r"\end{table}"))
            except Exception as e:
                print(f"[표 생성 실패: {e}]")

        else:
            # 일반 섹션
            text_exp = openai_utils.ask_question(
                f"'{creative_title}' 주제의 '{sec}' 섹션 작성, 최소 {min_words}단어 이상.",
                api_key=api_key
            )
            text = text_utils.clean_section_text(text_exp, remove_title=True, section_title=sec)
            text = text_utils.insert_cites(text, bib_keys)
            doc.append(NoEscape(text))

        doc.append(Command('newpage'))

    # 참고문헌
    doc.append(NoEscape(r"\bibliographystyle{apalike}"))
    doc.append(NoEscape(r"\bibliography{references}"))

    # 저장
    tex_file = "main.tex"
    doc.generate_tex(tex_file.replace(".tex", ""))

    # 자산 수집
    asset_files = []
    for folder in ["images", "graphs"]:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                asset_files.append(os.path.join(folder, file))

    return tex_file, "references.bib", asset_files, creative_title, research_topic
