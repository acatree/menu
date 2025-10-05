import re
from openai_utils import ask_question
def generate_bibtex(topic, num_refs=10, language="ko", api_key=None):
    """
    '{topic}' 관련 SCI/KCI 논문 BibTeX를 num_refs개 생성
    author, title, journal, year, volume, number, pages, doi 포함
    """
    entries = []

    for _ in range(num_refs):
        raw_entry = ask_question(
            f"Generate a complete BibTeX @article entry for a scientific paper on '{topic}'. "
            "Include all fields: author, title, journal, year, volume, number, pages, doi. "
            "Do not truncate or omit fields. Return only the BibTeX entry.",
            language=language,
            api_key=api_key
        )

        # 중첩 중괄호 포함 전체 BibTeX 블록 추출
        match = re.search(r'(@\w+\{(?:[^{}]|\{[^{}]*\})*\})', raw_entry, flags=re.DOTALL)
        if match:
            entries.append(match.group(1).strip())
    return entries
