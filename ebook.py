# ebook.py

import os
import csv
from pylatex import Document, Command, NoEscape
from translate import Translator
import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

# --- OpenAI helper functions ---
def ask_question(question):
    prompt = f"Question: {question}\nAnswer:"
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].text.strip()

def blogposting(topic):
    question = f"주제: [{topic}]\n단어 200개 분량의 유튜브 숏 대본을 작성하세요. 한국어로 작성."
    return ask_question(question)

# --- LaTeX generation ---
def generate_latex(TOPIC1, num_list):
    """
    Generates LaTeX file for the topic and returns the file path.
    """
    # Get topic list from OpenAI
    question2 = f'{TOPIC1} non duplicate topic list for Youtube shorts, {num_list} list, output as python list format'
    try:
        content2 = ask_question(question2)
        topic_list = eval(content2)
    except:
        topic_list = [TOPIC1 + f" {i+1}" for i in range(num_list)]

    to_list = topic_list[:num_list]

    # Create LaTeX document
    document = Document(documentclass='scrbook', document_options=['a5paper', 'pagesize', '10pt'])
    document.preamble.append(Command('usepackage', 'kotex'))

    # Title page
    title = f"{TOPIC1} eBook"
    subtitle = f"{TOPIC1} Subtopics"
    document.append(NoEscape(r"\begin{titlepage}"))
    document.append(NoEscape(f"\centering{{\\fontsize{{30}}{{48}}\selectfont {title}}}\\"))
    document.append(NoEscape(f"\centering{{\\fontsize{{18}}{{48}}\selectfont {subtitle}}}\\"))
    document.append(NoEscape(r"\end{titlepage}"))

    # Content sections
    for ii, topic in enumerate(to_list):
        sectiontitle = "\section*{" + str(ii+1) + ". " + topic + "/" + Translator(from_lang='en', to_lang='ko').translate(topic) + "}"
        document.append(NoEscape(sectiontitle))
        content = blogposting(topic)
        document.append(NoEscape(r"\large{" + content + "}"))
        document.append(Command('newpage'))

    # Save LaTeX file
    tex_folder = 'tex'
    os.makedirs(tex_folder, exist_ok=True)
    tex_path = os.path.join(tex_folder, f"{TOPIC1}.tex")
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(document.dumps())

    return tex_path
