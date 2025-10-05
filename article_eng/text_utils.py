import re, random

def clean_section_text(text, remove_title=False, section_title=""):
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = text.replace('**', '')
    if remove_title and section_title:
        text = re.sub(rf'^{section_title}\s*', '', text, flags=re.MULTILINE)
    return text.strip()

from openai_utils import ask_question

def extract_keywords(text, num=8, api_key=None, language="ko"):
    """
    텍스트에서 의미 있는 핵심 키워드 추출
    - OpenAI 모델 활용
    - num: 뽑을 키워드 개수
    - 쉼표로 구분된 문자열 반환
    """
    prompt = (
        f"다음 텍스트에서 의미 있는 핵심 키워드 {num}개만 추출하고, "
        "쉼표로 구분해서 출력해 주세요.\n\n"
        f"{text}"
    ) if language == "ko" else (
        f"Extract {num} most relevant keywords from the following text, "
        "and return them as a comma-separated list.\n\n"
        f"{text}"
    )

    keywords_text = ask_question(prompt, language=language, api_key=api_key)
    
    # 모델 출력 후 공백 제거, 단어별로 쉼표 연결
    keywords = [k.strip() for k in keywords_text.replace('\n','').split(',') if k.strip()]
    return ', '.join(keywords[:num])
    
def insert_cites(text, bib_keys, prob=0.2):
    import random
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for i, s in enumerate(sentences):
        if bib_keys and random.random() < prob:
            key = random.choice(bib_keys)
            sentences[i] = s + f" \\cite{{{key}}}"
    return ' '.join(sentences)
