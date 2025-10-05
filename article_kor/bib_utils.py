import re
from openai_utils import ask_question

def generate_bibtex(topic, num_refs=10, language="ko", api_key=None):
    entries = []
    for _ in range(num_refs):
        raw_entry = ask_question(
            f"'{topic}' 관련 SCI/KCI 논문 BibTeX 생성, author, title, journal, year, volume, pages 포함",
            language, api_key
        )
        match = re.search(r'(@\w+\{[^}]+\})', raw_entry, flags=re.DOTALL)
        if match:
            entries.append(match.group(1))
    return entries
