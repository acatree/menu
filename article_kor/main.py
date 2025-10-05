from pylatex import Document, Command, NoEscape
import os, re
import openai_utils, text_utils, figure_utils, bib_utils

def generate_paper(topic, api_key=None):
    """
    주제를 입력하면 창의적 연구 제목과 연구주제를 생성하고,
    각 섹션별 최소 글자 수를 조절하여 SCI/KCI 수준 논문 초안 생성
    분석 섹션에서는 실제 통계 데이터 + 수학적 모델 + 그래프 포함
    """
    # 1. 창의적 연구 제목/주제 생성
    creative_title = openai_utils.ask_question(
        f"'{topic}' 관련, 창의적이고 시도되지 않은 수학적 모델링이 가능한 연구 주제를 "
        "논문 제목 형식으로 생성해 주세요.",
        api_key=api_key
    )
    research_topic = openai_utils.ask_question(
        f"위 제목에 해당하는 연구 주제를 1~2문장으로 요약",
        api_key=api_key
    )

    # 2. LaTeX 설정
    doc = Document(documentclass='article', document_options=['12pt'])
    doc.packages.append(Command('usepackage','kotex'))
    doc.packages.append(Command('usepackage','geometry', options='a4paper,top=2.5cm,bottom=2.5cm,left=3cm,right=3cm'))
    doc.append(NoEscape(r'\setlength{\parskip}{0.5em}'))
    doc.append(NoEscape(r'\setlength{\parindent}{2em}'))

    # 3. 제목/저자
    doc.preamble.append(Command('title', creative_title))
    doc.preamble.append(Command('author', "강상규"))
    doc.append(NoEscape(r'\maketitle'))

    # 4. 초록/키워드
    doc.append(NoEscape(r'\section*{초록}'))
    abstract_text = openai_utils.ask_question(
        f"'{research_topic}' 초록 작성, 최소 180~220단어",
        api_key=api_key
    )
    doc.append(NoEscape(text_utils.clean_section_text(abstract_text)))

    doc.append(NoEscape(r'\section*{키워드}'))
    doc.append(NoEscape(text_utils.extract_keywords(abstract_text, api_key=api_key)))
    doc.append(Command('newpage'))

    # 5. BibTeX
    bib_entries = bib_utils.generate_bibtex(research_topic, 10, api_key=api_key)
    with open("references.bib",'w',encoding='utf-8') as f:
        f.write("\n\n".join(bib_entries))
    bib_keys = [re.search(r'@.*?\{(.*?),', e).group(1) for e in bib_entries if re.search(r'@.*?\{(.*?),', e)]

    # 6. 섹션 작성 (섹션별 최소 글자 수 설정)
    section_requirements = {
        "서론": 300,
        "관련 연구": 350,
        "연구 방법": 400,
        "분석": 500,
        "결론": 250
    }

    sections = ["서론","관련 연구","연구 방법","분석","결론"]
    for sec in sections:
        doc.append(NoEscape(f"\\section{{{sec}}}"))

        min_words = section_requirements.get(sec, 300)
        if sec == "분석":
            # 분석 섹션: 수학적 모델 + 실험/논의 + 그래프
            text_exp = openai_utils.ask_question(
                f"'{research_topic}' 분석 섹션 작성, 수학적 모델 포함, "
                f"실험 및 결과 + 논의 포함, 최소 {min_words}단어",
                api_key=api_key
            )
            text = text_utils.clean_section_text(text_exp, remove_title=True)
            doc.append(NoEscape(text))

            # 그래프
            fig = figure_utils.generate_graph(sec, research_topic, api_key=api_key)
            if fig:
                figure_utils.insert_figure(doc, fig, f"{sec} 관련 그래프")

            # 표
            table = figure_utils.generate_table(sec, research_topic, api_key=api_key)
            if table:
                doc.append(NoEscape(r"\begin{table}[h]"))
                doc.append(NoEscape(r"\centering"))
                doc.append(NoEscape(r"\resizebox{0.9\textwidth}{!}{" + table + "}"))
                doc.append(NoEscape(f"\\caption{{{sec} 관련 표}}"))
                doc.append(NoEscape(r"\end{table}"))

            # --- 6.1 데이터 생성 및 분석 ---
            data_prompt = (
                f"'{research_topic}' 관련 통계 데이터 예시를 생성하세요. "
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

            # --- 6.2 분석 텍스트 ---
            analysis_prompt = (
                f"'{research_topic}' 분석 섹션 작성, 위 데이터(df)를 이용, "
                f"수학적 모델 + 통계 분석 + 결과 해석 포함, 최소 {min_words}단어"
            )
            text_exp = openai_utils.ask_question(analysis_prompt, api_key=api_key)
            text = text_utils.clean_section_text(text_exp)
            doc.append(NoEscape(text))

            # --- 6.3 그래프 ---
            if df is not None:
                fig = figure_utils.generate_graph_from_df(sec, df, research_topic)
                if fig:
                    figure_utils.insert_figure(doc, fig, f"{sec} 관련 그래프")

            # --- 6.4 표 ---
            if df is not None:
                table_latex = df.to_latex(index=False)
                doc.append(NoEscape(r"\begin{table}[h]"))
                doc.append(NoEscape(r"\centering"))
                doc.append(NoEscape(r"\resizebox{0.9\textwidth}{!}{" + table_latex + "}"))
                doc.append(NoEscape(f"\\caption{{{sec} 관련 표}}"))
                doc.append(NoEscape(r"\end{table}"))

        else:
            # 나머지 섹션
            text_exp = openai_utils.ask_question(
                f"'{research_topic}' '{sec}' 섹션 작성, 최소 {min_words}단어",
                api_key=api_key
            )
            text = text_utils.clean_section_text(text_exp, remove_title=True, section_title=sec)
            text = text_utils.insert_cites(text, bib_keys)
            doc.append(NoEscape(text))

        # 모든 섹션 이미지 삽입
#        imgs = figure_utils.generate_images(api_key, research_topic, sec)
#        for img in imgs:
#            figure_utils.insert_figure(doc, img, f"{sec} 관련 이미지")

        doc.append(Command('newpage'))

    # 7. 참고문헌
    doc.append(NoEscape(r"\bibliographystyle{apalike}"))
    doc.append(NoEscape(r"\bibliography{references}"))

    # 8. LaTeX 저장
    tex_file = f"{creative_title}.tex"
    doc.generate_tex(tex_file.replace(".tex",""))

    # 9. 이미지와 그래프 파일 수집
    asset_files = []
    for folder in ["images", "graphs"]:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                asset_files.append(os.path.join(folder, file))

    # 10. 반환
    return tex_file, "references.bib", asset_files, creative_title, research_topic
