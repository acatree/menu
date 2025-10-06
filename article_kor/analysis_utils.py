# analysis_utils.py
import pandas as pd
import numpy as np
from . import openai_utils, figure_utils, text_utils
from .latex_utils import finalize_latex_output
from pylatex import NoEscape, Command

def generate_analysis_section(doc, creative_title, sec, min_words, api_key=None):
    local_env = {"pd": pd, "np": np}
    df = None

    # 1. 데이터 생성
    data_prompt = (
        f"'{creative_title}' 관련 통계 데이터 예시 생성. "
        "pandas DataFrame(df) 5~6개 열, 20~30행 포함."
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
            "변수3": np.random.normal(0, 1, 20),
            "변수4": np.linspace(1, 10, 20),
            "변수5": np.random.choice(["A", "B", "C"], 20)
        })

    # 2. 분석 텍스트 작성
    analysis_prompt = (
        f"'{creative_title}' '{sec}' 섹션 작성. df 기반 모델링/통계/해석, 최소 {min_words}단어 이상."
    )
    text_exp = openai_utils.ask_question(analysis_prompt, api_key=api_key)
    text = text_utils.clean_section_text(text_exp)
    text = finalize_latex_output(text)

    doc.append(NoEscape(text))

    # 3. 그래프
    try:
        fig = figure_utils.generate_graph_from_df(sec, df, creative_title)
        if fig:
            figure_utils.insert_figure(doc, fig, f"{sec} 관련 그래프", placement='H')
    except Exception as e:
        print(f"[그래프 생성 실패: {e}]")

    # 4. 표
    try:
        table_latex = df.to_latex(index=False, longtable=False, caption=f"{sec} 관련 표", label=f"tab:{sec}")
        doc.append(NoEscape(r"\begin{table}[H]\centering" + table_latex + r"\end{table}"))
    except Exception as e:
        print(f"[표 생성 실패: {e}]")

    # 섹션 끝 페이지 나누기
    doc.append(Command('newpage'))

    return df
