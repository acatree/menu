from pylatex import Document, Section, Subsection, Command, Math, Figure
from pylatex.utils import bold, NoEscape
import csv
import json
import openai
import os
import markdown
from translate import Translator
import requests
import urllib.request
from config import *
openai.api_key = "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"


def ask_question(question):
    prompt = f"Question: {question}\nAnswer:"
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=1024, # limit the maximum number of tokens the model can generate
        n=1, # only generate one response
        stop=None, # don't specify a stop sequence
        temperature=0.5, # set the temperature of the model
    )
    answer = response.choices[0].text.strip()
    return answer

def blogposting(TOPIC):
    translator = Translator(from_lang='ko',to_lang='en')
    question1 ='주제 : ['+TOPIC+']\n단어의 개수 200개 분량의 대본은 작성해야 합니다:\n 대본은 다음 기준을 따라야 합니다:\n 최초 진술은 뉴스 헤드라인 형식의 50자 이내의 제목과 관련된 흥미롭고 놀라운 사실이어야 합니다.\n 최초 진술에 대한 후속 진술은 최초 진술을 뒷받침하는 과학적 사실 또는 역사적 증거입니다.\n 동영상의 본문은 논의 중인 주제에 대한 추가 설명이 들어갑니다. 추가 설명에는 최초 진술에 덧붙일 과학적 사실과 역사적 증거에 대한 것이 포함됩니다 대본에는 이야기 내용만 포함되어야 하며 카메라 촬영 및 장면 전환과 같은 추가적인 스크립트 기능은 포함되지 않습니다. 각 문장은 구체적이어야 하고, 간결해야 하며 전문적인 언어를 사용해야 합니다\n 한국어로 작성'
    content1 = ask_question(question1)
    sentence=content1
    print(sentence)
    return (sentence)


TOPIC1 = 'IT'
question2 = TOPIC1 +' non duplicate topic list for Youtube shorts, 5 list, output as python list format'
content2 = ask_question(question2)
magical_creatures = content2
magical_creatures = eval(magical_creatures)
csv_file = TOPIC1+'.csv'
# Write the list to the CSV file
with open(csv_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Magical Creature'])
    writer.writerows([[creature] for creature in magical_creatures])

file = open(csv_file, 'r', encoding='utf-8', newline='')
reader = csv.reader(file)
data = list(reader)
topic_list=[]
for row in data:
    topic_list.append(row[0])
file.close()

import csv
def read_csv_as_list(file_path):
    data = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            data.append(row)
    return data

# Example usage:
file_path = TOPIC1+'.csv'  # Replace 'example.csv' with your CSV file path
csv_data = read_csv_as_list(file_path)
flat_list = [inner[0] for inner in csv_data]
unique_list = list(set(flat_list))
print(unique_list)
len(unique_list)
topic_list=unique_list
to_list=topic_list[0:50]
to_list

document = Document(documentclass='scrbook', document_options=['a5paper', 'pagesize', '10pt', 'bibtotoc', 'pointlessnumbers', 'normalheadings', 'DIV=9', 'twoside=false'])
document.preamble.append(Command('usepackage', 'graphicx'))
document.preamble.append(Command('usepackage', 'float'))
document.preamble.append(Command('KOMAoptions', 'DIV=last'))
document.preamble.append(Command('usepackage', 'trajan'))
document.preamble.append(Command('usepackage', 'mathpazo', 'sc'))
document.preamble.append(Command('linespread', '1.05'))
document.preamble.append(Command('usepackage', 'verbatim'))
document.preamble.append(Command('usepackage', 'listings'))
document.preamble.append(Command('usepackage', 'blindtext'))
document.preamble.append(Command('usepackage', 'float'))
document.preamble.append(Command('usepackage', 'kotex'))

# Title page
title = '[ebook의 제목을 입력합니다]'
title ="\centering{\\fontsize{30}{48}\selectfont "+title+"}\\\ "
subtitle ='[ebook의 부제목을 입력합니다]'
subtitle="\centering{\\fontsize{18}{48}\selectfont "+subtitle+"}\\\ "
document.append(Command('begin','titlepage'))
document.append(NoEscape(title))
document.append(Command('vspace','10mm'))
document.append(NoEscape(subtitle))
document.append(Command('vspace','15mm'))
document.append(NoEscape(r"\centering{\Large{Calamari}}\\"))
document.append(Command('vspace',Command('fill')))
document.append(Command('end','titlepage'))

# Empty page
document.append(Command('newpage'))
document.append(Command('thispagestyle','empty'))
document.append(Command('vspace*','2cm'))
document.append(Command('begin','center'))
document.append(NoEscape(r"\centering{{\fontsize{20}{48}\selectfont Preface}}\\"))
document.append(Command('vspace','20mm'))
document.append(NoEscape(r"\Large{\parbox{10cm}{"))
document.append(NoEscape(r"\begin{raggedright}"))

introduction = "[ebook의 소개정보를 입력합니다] 이 시리즈는 특정 주제와 그에 해당되는 짧은 50개의 소개글을 실은 자료 서적입니다. 스크립트는 OpenAI를 통해 만들어 졌습니다."
introduction="{\Large \\textit{"+introduction+"}}"
document.append(NoEscape(introduction))
document.append(NoEscape(r'\vspace{.5cm}\hfill{}'))
document.append(NoEscape(r"\end{raggedright}}}"))
document.append(Command('end','center'))
document.append(Command('newpage'))

#contents
for ii in range(len(to_list)):
    TOPIC=to_list[ii]
    (content) = blogposting(TOPIC)
    sectiontitle="\section*{"+str(ii+1)+". "+TOPIC+"/"+Translator(from_lang='en',to_lang='ko').translate(TOPIC)+"}"
    document.append(NoEscape(sectiontitle))
    content="\large{"+content+"}"
    document.append(NoEscape(content))
    document.append(Command('newpage'))

#file
title = Translator(from_lang='ko',to_lang='en').translate(TOPIC1)
tex_path=f'tex/{title}.tex'
latex_code = document.dumps()
if latex_code is not None and isinstance(latex_code, str):
    with open(tex_path, 'w', encoding='utf-8') as file:
        file.write(latex_code)
else:
    print("Error: Invalid LaTeX code.")
