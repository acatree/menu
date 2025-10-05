import re
from openai_utils import ask_question

def generate_bibtex(topic, num_refs=10, language="ko", api_key=None):
    """
    '{topic}' 관련 SCI/KCI 논문 BibTeX를 num_refs개 생성
    citation key를 숫자순(ref1, ref2, ...)으로 지정
    """
    entries = []
    for i in range(1, num_refs + 1):
        raw_entry = ask_question(
            f"Generate a complete BibTeX @article entry for a scientific paper on '{topic}'. "
            "Include all fields: author, title, journal, year, volume, number, pages, doi. "
            "Do not truncate or omit fields. Return only the BibTeX entry.",
            language=language,
            api_key=api_key
        )
        # 중첩 중괄호 포함 전체 BibTeX 블록 추출
        match = re.search(r'@(\w+)\{([^,]+),', raw_entry)
        if match:
            entry_type = match.group(1)  # @article, @book 등
            # 숫자 기반 citation key 생성
            new_key = f"ref{i}"
            # 원본 key를 숫자 key로 치환
            entry_fixed = re.sub(r'@' + entry_type + r'\{[^,]+,', f"@{entry_type}{{{new_key},", raw_entry, count=1)
            entries.append(entry_fixed.strip())
    return entries                                                                                
