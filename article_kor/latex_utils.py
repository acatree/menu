import re
def escape_latex_special_chars(text):
    commands = re.findall(r"\\[a-zA-Z]+(\{.*?\})*", text)
    placeholders = [f"__CMD{i}__" for i in range(len(commands))]
    
    for ph, cmd in zip(placeholders, commands):
        text = text.replace(cmd, ph)

    replacements = {
        '%': r'\%',
        '$': r'\$',
        '&': r'\&',
        '_': r'\_',
        '~': r'\~{}',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    # LaTeX 명령어 복원
    for ph, cmd in zip(placeholders, commands):
        text = text.replace(ph, cmd)
    
    return text

def convert_text_table_to_latex(text):
    """
    텍스트 형태 표 자동 변환 → LaTeX tabular 환경
    """
    pattern = re.compile(
        r"(?P<intro>[^\n]*?(?:averaged|mean|median|variable|summary)[^\n]*?\n)"
        r"(?P<table>(?:[^\n]*\t[^\n]*\n)+)", re.IGNORECASE
    )

    def make_table(match):
        intro = match.group("intro").strip()
        table_text = match.group("table").strip()

        intro = escape_latex_special_chars(intro)
        rows = table_text.splitlines()
        header = rows[0].split("\t")
        body = rows[1:]

        latex = []
        latex.append(r"\noindent " + intro + "\n")
        latex.append(r"\begin{table}[H]")
        latex.append(r"\centering")
        latex.append(r"\caption{Summary Statistics}")
        latex.append(r"\begin{tabular}{l" + "c" * (len(header) - 1) + r"}")
        latex.append(r"\toprule")
        latex.append(" & ".join(header) + r" \\")
        latex.append(r"\midrule")
        for row in body:
            latex.append(" & ".join(row.split("\t")) + r" \\")
        latex.append(r"\bottomrule")
        latex.append(r"\end{tabular}")
        latex.append(r"\end{table}")

        return "\n".join(latex)
    return re.sub(pattern, make_table, text)

def finalize_latex_output(text):
    text = re.sub(r"^\s*(초록|Abstract)[:：]?\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
    # 표 변환 전에 escape
    text = escape_latex_special_chars(text)
    # 표 변환
    text = convert_text_table_to_latex(text)
    return text
