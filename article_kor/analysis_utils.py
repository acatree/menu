import pandas as pd
import numpy as np
from . import openai_utils, figure_utils, text_utils
from pylatex import NoEscape, Command

def generate_synthetic_data_for_model(topic):
    """
    주제에 맞는 테스트용 수학 모델 데이터 생성
    - 회귀, 상관, 시계열 등 기본적 패턴 반영
    """
    np.random.seed(42)

    if "회귀" in topic or "상관" in topic:
        x = np.linspace(0, 10, 50)
        y = 2.5 * x + np.random.normal(0, 2, size=len(x))
        df = pd.DataFrame({"입력값_x": x, "출력값_y": y})
    
    elif "시계열" in topic or "시간" in topic:
        t = np.arange(1, 51)
        y = 100 + 3 * t + 10 * np.sin(0.3 * t) + np.random.normal(0, 5, 50)
        df = pd.DataFrame({"시간": t, "값": y})
    
    elif "분류" in topic or "클러스터" in topic:
        x1 = np.random.normal(0, 1, 50)
        x2 = np.random.normal(5, 1, 50)
        labels = ["A"]*25 + ["B"]*25
        df = pd.DataFrame({"특징1": np.concatenate([x1[:25], x2[:25]]),
                           "특징2": np.concatenate([x1[25:], x2[25:]]),
                           "클래스": labels})
    
    else:
        # 일반 데이터 (랜덤)
        df = pd.DataFrame({
            "변수1": np.random.rand(30),
            "변수2": np.random.randint(10, 100, 30),
            "변수3": np.random.normal(0, 1, 30),
        })

    return df


def generate_analysis_section(doc, creative_title, sec, min_words, api_key=None):
    """
    '분석' 섹션 전용 생성
    - 수학 모델 기반 가상 데이터 생성
    - GPT 분석 텍스트 작성 (필요 시 LaTeX 소제목 자동 포함)
    - 그래프/표 삽입
    """
    # 1. 수학 모델용 테스트 데이터 생성
    df = generate_synthetic_data_for_model(creative_title)

    # 2. GPT 분석 텍스트 작성
    analysis_prompt = (
        f"'{creative_title}' 주제의 '{sec}' 섹션을 작성하라. "
        f"다음 데이터는 이 주제에 대한 수학 모델의 테스트용 데이터이다. "
        f"모델의 가정, 추정, 해석, 결론을 단계적으로 설명하라. "
        f"필요하다면 LaTeX 소제목(예: '\\subsection{{모델 개요}}')을 사용하여 논리적으로 구분하라. "
        f"단, 본문은 하나로 이어지게 자연스럽게 작성하라. "
        f"최소 {min_words}단어 이상으로 작성하라.\n\n"
        f"데이터 요약 (상위 5개 행):\n{df.head().to_string(index=False)}\n\n"
        f"데이터 컬럼 설명: {', '.join(df.columns)}\n"
        "이 데이터를 수학적 또는 통계적으로 해석하는 학술 분석을 작성하라."
    )

    text_exp = openai_utils.ask_question(analysis_prompt, api_key=api_key)
    text = text_utils.clean_section_text(text_exp)

    # GPT가 \subsection 등 LaTeX 명령어를 직접 포함할 수 있음 → NoEscape 사용
    doc.append(NoEscape(text))

    # 3. 그래프 생성 및 삽입
    try:
        fig = figure_utils.generate_graph_from_df(sec, df, creative_title)
        if fig:
            figure_utils.insert_figure(doc, fig, f"{sec} 관련 그래프", placement='H')
    except Exception as e:
        print(f"[그래프 생성 실패: {e}]")

    # 4. 표 삽입
    try:
        table_latex = df.to_latex(index=False, longtable=False, caption=f"{sec} 관련 데이터 요약", label=f"tab:{sec}")
        doc.append(NoEscape(r"\begin{table}[H]\centering" + table_latex + r"\end{table}"))
    except Exception as e:
        print(f"[표 생성 실패: {e}]")

    # 섹션 끝에 페이지 나누기
    doc.append(Command('newpage'))

    return df
