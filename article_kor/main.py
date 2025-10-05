from pylatex import Document, Command, NoEscape
import zipfile
import os
import openai_utils, text_utils, figure_utils, bib_utils

def generate_paper(title, topic, api_key=None):
    # 단 1개, LaTeX 설정
    doc = Document(documentclass='article', document_options=['12pt'])
    doc.packages.append(Command('usepackage','kotex'))
    doc.packages.append(Command('usepackage','geometry', options='a4paper,top=2.5cm,bottom=2.5cm,left=3cm,right=3cm'))
    doc.append(NoEscape(r'\setlength{\parskip}{0.5em}'))
    doc.append(NoEscape(r'\setlength{\parindent}{2em}'))

    # 제목/저자
    doc.preamble.append(Command('title', title))
    doc.preamble.append(Command('author', "강상규"))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))

    # 초록/키워드
    doc.append(NoEscape(r'\section*{초록}'))
    doc.append(NoEscape(text_utils.clean_section_text(
        openai_utils.ask_question(f"'{topic}' 초록 작성, 150~200단어", api_key=api_key)
    )))
    doc.append(NoEscape(r'\section*{주제}'))
    doc.append(NoEscape(text_utils.extract_keywords(
        openai_utils.ask_question(f"'{topic}' 키워드 8개 생성", api_key=api_key)
    )))
    doc.append(Command('newpage'))

    # BibTeX
    bib_entries = bib_utils.generate_bibtex(topic, 10, api_key=api_key)
    with open("references.bib",'w',encoding='utf-8') as f:
        f.write("\n\n".join(bib_entries))
    bib_keys = [re.search(r'@.*?\{(.*?),', e).group(1) for e in bib_entries if re.search(r'@.*?\{(.*?),', e)]

    # 섹션 작성
    sections = ["서론","관련 연구","연구 방법","실험 및 결과","논의","결론"]
    for sec in sections:
        doc.append(NoEscape(f"\\section{{{sec}}}"))
        text = openai_utils.ask_question(f"'{topic}' '{sec}' 섹션 작성, 최소 300단어", api_key=api_key)
        text = text_utils.clean_section_text(text, remove_title=True, section_title=sec)
        text = text_utils.insert_cites(text, bib_keys, prob=0.2)
        doc.append(NoEscape(text))

        # 그래프, 이미지, 표
        if sec in ["실험 및 결과","연구 방법"]:
            fig = figure_utils.generate_graph(sec, topic, api_key=api_key)
            if fig:
                figure_utils.insert_figure(doc, fig, f"{sec} 관련 그래프")

        table = figure_utils.generate_table(sec, topic, api_key=api_key)
        if table:
            doc.append(NoEscape(r"\begin{table}[h]"))
            doc.append(NoEscape(r"\centering"))
            doc.append(NoEscape(r"\resizebox{0.9\textwidth}{!}{" + table + "}"))
            doc.append(NoEscape(f"\\caption{{{sec} 관련 표}}"))
            doc.append(NoEscape(r"\end{table}"))

        imgs = figure_utils.generate_images(api_key, topic, sec)
        for img in imgs:
            figure_utils.insert_figure(doc, img, f"{sec} 관련 이미지")

        doc.append(Command('newpage'))

    doc.append(NoEscape(r"\bibliographystyle{apalike}"))
    doc.append(NoEscape(r"\bibliography{references}"))

    # LaTeX 저장 및 ZIP
    tex_file = f"{title}.tex"
    doc.generate_tex(tex_file.replace(".tex",""))
    zip_file = f"{title}_files.zip"
    with zipfile.ZipFile(zip_file,'w',zipfile.ZIP_DEFLATED) as zf:
        zf.write(tex_file)
        zf.write("references.bib")
        for folder in ["images","graphs"]:
            if os.path.exists(folder):
                for file in os.listdir(folder):
                    zf.write(os.path.join(folder,file), arcname=os.path.join(folder,file))
    return tex_file, "references.bib", zip_file
