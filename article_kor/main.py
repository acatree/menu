import sys, os
sys.path.append(os.path.dirname(__file__))  # main.py 기준
from pylatex import Document, Command, NoEscape
import os, re
from . import openai_utils
from . import text_utils
from . import figure_utils
from . import bib_utils

def generate_paper(topic, api_key=None):
    """
    주제를 입력하면 창의적 연구 제목과 연구주제를 생성하고,
    각 섹션별 최소 글자 수를 조절하여 SCI/KCI 수준 논문 초안 생성
    분석 섹션에서는 실제 통계 데이터 + 수학적 모델 + 그래프 포함
    """

    # 1. 창의적 연구 제목/주제 생성
    creative_title = openai_utils.ask_question(
        f"'{topic}'와 직접적으로 관련되면서도, 창의적이고 "
        "아직 시도되지 않은 수학적 모델링이 가능한 연구 논문 제목을 "
        "하나 생성해 주세요. 인용부호(따옴표)는 포함하지 마세요.",
        api_key=api_key
    ).strip().replace('"', '').replace("'", "")

    research_topic = openai_utils.ask_question(
        f"'{creative_title}'에 해당하는 연구 주제를 1~2문장으로 요약해 주세요.",
        api_key=api_key
    )

    # 2. LaTeX 설정
    doc = Document(documentclass='article', document_options=['12pt'])
    doc.packages.append(Command('usepackage', 'kotex'))
    doc.packages.append(Command('usepackage', 'geometry', options='a4paper,top=2.5cm,bottom=2.5cm,left=3cm,right=3cm'))
    doc.append(NoEscape(r'\setlength{\parskip}{0.5em}'))
    doc.append(NoEscape(r'\setlength{\parindent}{2em}'))

    # 3. 제목/저자/날짜
    doc.preamble.append(Command('title', creative_title))
    doc.preamble.append(Command('author', "강상규"))
    doc.preamble.append(Command('date', ""))  # 날짜 공란
    doc.append(NoEscape(r'\maketitle'))

    # 4. 초록/키워드
    doc.append(NoEscape(r'\section*{초록}'))
    abstract_text = openai_utils.ask_question(
        f"'{research_topic}'에 대한 논문 초록을 작성하세요. "
        "내용은 전문적이고 논리적 흐름이 있어야 하며, 180~220단어 사이로 작성해 주세요.",
        api_key=api_key
    )
    doc.append(NoEscape(text_utils.clean_section_text(abstract_text)))

    doc.append(NoEscape(r'\section*{키워드}'))
    doc.append(NoEscape(text_utils.extract_keywords(abstract_text, api_key=api_key)))
    doc.append(Command('newpage'))

    # 5. 참고문헌 생성
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

    subtopic_prompts = {
        "서론": "연구 배경, 필요성, 연구 목적을 중심으로 소제목을 포함해 구성하세요.",
        "관련 연구": "선행연구 검토, 차별점, 한계 분석 등의 소제목을 포함하세요.",
        "연구 방법": "이론적 모델, 가정, 실험 설계 등의 소제목을 포함하세요.",
        "분석": "모델 결과, 데이터 해석, 통계 검증 등의 소제목을 포함하세요.",
        "결론": "요약, 시사점, 연구 한계와 향후 과제의 소제목을 포함하세요."
    }

    sections = ["서론", "관련 연구", "연구 방법", "분석", "결론"]
    for sec in sections:
        doc.append(NoEscape(f"\\section{{{sec}}}"))
        min_words = section_requirements.get(sec, 300)
        extra_prompt = subtopic_prompts.get(sec, "")

        if sec == "분석":
            # --- 6.1 데이터 생성 ---
            data_prompt = (
                f"'{creative_title}' 주제와 관련된 통계 데이터 예시를 생성하세요. "
                "pandas DataFrame 형식으로, 5~6개 변수, 20~30개 샘플 포함. "
                "변수 이름과 의미를 명시하세요."
            )
            data_code = openai_utils.ask_question(data_prompt, api_key=api_key)

            import pandas as pd, numpy as np
            local_env = {"pd": pd, "np": np}
            df = None
            try:
                exec(data_code, local_env)
                df = local_env.get('df', None)
            except Exception as e:
                print(f"[데이터 생성 실패]: {e}")
                df = None

            # --- 6.2 데이터 기반 분석 (중복 제거 후 단일) ---
            analysis_prompt = (
                f"'{creative_title}'의 '{sec}' 섹션을 작성하세요. "
                "생성된 데이터(df)를 기반으로 수학적 모델링, 통계 분석, 결과 해석을 포함하고, "
                f"{extra_prompt} 최소 {min_words}단어 이상."
            )
            text_exp = openai_utils.ask_question(analysis_prompt, api_key=api_key)
            text = text_utils.clean_section_text(text_exp)
            doc.append(NoEscape(text))

            # --- 6.3 그래프 / 표 ---
            if df is not None:
                fig = figure_utils.generate_graph_from_df(sec, df, creative_title)
                if fig:
                    figure_utils.insert_figure(doc, fig, f"{sec} 관련 그래프")

                table_latex = df.to_latex(index=False)
                doc.append(NoEscape(r"\begin{table}[h]"))
                doc.append(NoEscape(r"\centering"))
                doc.append(NoEscape(r"\resizebox{0.9\textwidth}{!}{" + table_latex + "}"))
                doc.append(NoEscape(f"\\caption{{{sec} 관련 표}}"))
                doc.append(NoEscape(r"\end{table}"))

        else:
            # --- 일반 섹션 ---
            text_exp = openai_utils.ask_question(
                f"'{creative_title}' 주제의 '{sec}' 섹션을 작성하세요. "
                f"{extra_prompt} 최소 {min_words}단어 이상.",
                api_key=api_key
            )
            text = text_utils.clean_section_text(text_exp, remove_title=True, section_title=sec)
            text = text_utils.insert_cites(text, bib_keys)
            doc.append(NoEscape(text))

        doc.append(Command('newpage'))

    # 7. 참고문헌
    doc.append(NoEscape(r"\bibliographystyle{apalike}"))
    doc.append(NoEscape(r"\bibliography{references}"))

    # 8. 저장
    tex_file = "main.tex"
    doc.generate_tex(tex_file.replace(".tex", ""))

    # 9. 자산 수집
    asset_files = []
    for folder in ["images", "graphs"]:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                asset_files.append(os.path.join(folder, file))

    # 10. 반환
    return tex_file, "references.bib", asset_files, creative_title, research_topic
