# analysis_utils.py
import pandas as pd
import numpy as np
from . import openai_utils, figure_utils, text_utils
from .latex_utils import finalize_latex_output
from pylatex import NoEscape, Command

def fetch_real_data(topic):
    """
    주제에 맞는 실제 데이터 불러오기
    - CSV, Excel, API 등
    - 실제 사용 시 데이터 소스에 맞게 URL/API 수정 필요
    """
    try:
        if "인구" in topic:
            url = "https://example.com/population.csv"  # 실제 데이터 URL 필요
            df = pd.read_csv(url)
        elif "경제" in topic:
            url = "https://example.com/economic.csv"  # 실제 데이터 URL 필요
            df = pd.read_csv(url)
        else:
            # fallback: 작은 예시 데이터
            df = pd.DataFrame({
                "변수1": np.random.rand(20),
                "변수2": np.random.randint(10, 100, 20),
                "변수3": np.random.normal(0, 1, 20),
                "변수4": np.linspace(1, 10, 20),
                "변수5": np.random.choice(["A", "B", "C"], 20)
            })
    except Exception as e:
        print(f"[데이터 불러오기 실패, 예시 데이터 사용]: {e}")
        df = pd.DataFrame({
            "변수1": np.random.rand(20),
            "변수2": np.random.randint(10, 100, 20),
            "변수3": np.random.normal(0, 1, 20),
            "변수4": np.linspace(1, 10, 20),
            "변수5": np.random.choice(["A", "B", "C"], 20)
        })
    return df


def generate_analysis_section(doc, creative_title, sec, min_words, api_key=None):
    """
    '분석' 섹션 전용 생성
    - 실제 데이터 fetch
    - 분석 텍스트 작성
    - 그래프/표 LaTeX 삽입
    """
    # 1. 실제 데이터 불러오기
    df = fetch_real_data(creative_title)

    # 2. GPT 분석 텍스트 작성
    analysis_prompt = (
        f"'{creative_title}' '{sec}' 섹션 작성. "
        f"다음 데이터를 기반으로 모델링, 통계, 해석을 서술하고, 최소 {min_words}단어 이상 작성:\n\n"
        f"{df.head(5).to_string()}\n\n"
        "데이터 전체를 참고하여 분석 텍스트를 작성하되, 수치와 경향을 설명하고 결론을 포함하세요."
    )

    text_exp = openai_utils.ask_question(analysis_prompt, api_key=api_key)
    text = text_utils.clean_section_text(text_exp)
    text = finalize_latex_output(text)

    doc.append(NoEscape(text))

    # 3. 그래프 생성
    try:
        fig = figure_utils.generate_graph_from_df(sec, df, creative_title)
        if fig:
            figure_utils.insert_figure(doc, fig, f"{sec} 관련 그래프", placement='H')
    except Exception as e:
        print(f"[그래프 생성 실패: {e}]")

    # 4. 표 삽입
    try:
        table_latex = df.to_latex(index=False, longtable=False, caption=f"{sec} 관련 표", label=f"tab:{sec}")
        doc.append(NoEscape(r"\begin{table}[H]\centering" + table_latex + r"\end{table}"))
    except Exception as e:
        print(f"[표 생성 실패: {e}]")

    # 섹션 끝 페이지 나누기
    doc.append(Command('newpage'))

    return df
