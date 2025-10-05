import re, random

def clean_section_text(text, remove_title=False, section_title=""):
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = text.replace('**', '')
    if remove_title and section_title:
        text = re.sub(rf'^{section_title}\s*', '', text, flags=re.MULTILINE)
    return text.strip()

def extract_keywords(text, num=8):
    words = re.findall(r'\b[가-힣A-Za-z0-9\-]+\b', text)
    return ', '.join(words[:num])

def insert_cites(text, bib_keys, prob=0.2):
    import random
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for i, s in enumerate(sentences):
        if bib_keys and random.random() < prob:
            key = random.choice(bib_keys)
            sentences[i] = s + f" \\cite{{{key}}}"
    return ' '.join(sentences)
