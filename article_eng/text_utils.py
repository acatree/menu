import re, random
from openai_utils import ask_question

def clean_section_text(text, remove_title=False, section_title=""):
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = text.replace('**', '')
    if remove_title and section_title:
        text = re.sub(rf'^{section_title}\s*', '', text, flags=re.MULTILINE)
    return text.strip()

def extract_keywords(text, num=8, api_key=None, language="en"):
    prompt = (
        f"Extract {num} most relevant keywords from the following text, "
        "focusing on economics or real estate context. "
        "Return them as a comma-separated list.\n\n"
        f"{text}"
    )

    keywords_text = ask_question(prompt, language=language, api_key=api_key)

    # Clean up and return first 'num' keywords
    keywords = [k.strip() for k in keywords_text.replace('\n','').split(',') if k.strip()]
    return ', '.join(keywords[:num])

def insert_cites(text, bib_keys, prob=0.2):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for i, s in enumerate(sentences):
        if bib_keys and random.random() < prob:
            key = random.choice(bib_keys)
            sentences[i] = s + f" \\cite{{{key}}}"
    return ' '.join(sentences)
