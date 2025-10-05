import os
import io
import requests
import contextlib
import matplotlib.pyplot as plt
import openai
from openai import OpenAI
from pylatex import Document, Command, NoEscape

openai.api_key = None  # To be set dynamically (via Flask or environment variable)

# ---------------------------
# ChatGPT Request Function
# ---------------------------
def ask_question(question, language="en"):
    system_prompt = (
        "You are an expert academic writer specializing in SCI-level research papers."
        if language == "en"
        else "당신은 SCI/KCI 수준의 한국어 학술 논문 작성 전문가입니다."
    )
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.7,
        max_completion_tokens=3000,
    )
    return response.choices[0].message.content.strip()


# ---------------------------
# Visual Image Generation (DALL·E)
# ---------------------------
def generate_images(api_key, topic, section_title, count=1):
    client = OpenAI(api_key=api_key)
    os.makedirs("images", exist_ok=True)
    image_files = []

    for i in range(count):
        prompt = (
            f"A visual scene illustrating the section '{section_title}' on the topic '{topic}'. "
            f"Use descriptive or abstract style, without showing real people or brands. "
            f"Variation {i+1}."
        )
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
        )

        image_url = response.data[0].url if response.data and response.data[0].url else None
        if not image_url:
            raise ValueError("❌ Failed to generate image URL.")
        data = requests.get(image_url).content

        filename = f"images/{section_title.replace(' ', '_')}_image{i+1}.png"
        with open(filename, "wb") as f:
            f.write(data)
        image_files.append(filename)

    return image_files


# ---------------------------
# Graph Generation (Matplotlib)
# ---------------------------
def generate_graph(section_title, topic, figure_number=1):
    os.makedirs("graphs", exist_ok=True)
    file_path = f"graphs/{section_title.replace(' ', '_')}_fig{figure_number}.png"

    question = (
        f"Generate executable matplotlib code to visualize a graph relevant to "
        f"the section '{section_title}' in the topic '{topic}'. "
        f"Figure number: {figure_number}. Include an English caption. "
        f"Return full Python code."
    )
    code = ask_question(question, "en")

    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            exec(code, {"plt": plt})
        plt.savefig(file_path)
        plt.close()
    except Exception as e:
        print(f"[⚠ Graph generation failed] {section_title}: {e}")
        return ""

    return file_path


# ---------------------------
# Table Generation (LaTeX)
# ---------------------------
def generate_table(section_title, topic, table_number=1):
    question = (
        f"Generate LaTeX tabular code for a table relevant to section '{section_title}' "
        f"on the topic '{topic}'. Table number {table_number}, with English caption."
    )
    table_code = ask_question(question, "en")
    return table_code


# ---------------------------
# Bibliography (BibTeX)
# ---------------------------
def generate_bibtex(topic, num_refs=10):
    entries = []
    for i in range(num_refs):
        question = f"Generate 1 BibTeX entry for a recent SCI-level paper related to '{topic}'."
        entry = ask_question(question, "en")
        entries.append(entry)
    return entries


# ---------------------------
# Full Paper Generation
# ---------------------------
def generate_paper(title, topic, api_key=None, references=10):
    sections = ["Introduction", "Related Work", "Methodology", "Experiments and Results", "Discussion", "Conclusion"]

    doc = Document(documentclass="article", document_options=["12pt"])
    doc.packages.append(Command("usepackage", "setspace"))
    doc.packages.append(Command("usepackage", "geometry", options="margin=1in"))
    doc.packages.append(Command("usepackage", "graphicx"))

    doc.preamble.append(Command("title", title))
    doc.preamble.append(Command("author", "Sangkyu Kang"))
    doc.preamble.append(Command("date", NoEscape(r"\today")))
    doc.append(NoEscape(r"\maketitle"))
    doc.append(NoEscape(r"\tableofcontents"))
    doc.append(Command("newpage"))

    figure_counter = 1
    table_counter = 1
    generated_files = []

    for section in sections:
        doc.append(NoEscape(f"\\section{{{section}}}"))
        body_text = ask_question(
            f"Write the '{section}' section (at least 300 words) for the topic '{topic}', "
            "in a formal academic tone suitable for SCI journals.",
            "en",
        )
        doc.append(NoEscape(body_text))

        # --------------------------
        # Commented Figure Insertion
        # --------------------------
        doc.append(NoEscape(f"% Figure {figure_counter}: Matplotlib graph"))
        graph_file = generate_graph(section, topic, figure_counter)
        if graph_file:
            generated_files.append(graph_file)
        figure_counter += 1

        doc.append(NoEscape(f"% Figure {figure_counter}: DALL·E visual image"))
        image_files = generate_images(api_key, topic, section, count=1)
        generated_files.extend(image_files)
        figure_counter += 1
        # --------------------------

        # Table
        table_code = generate_table(section, topic, table_counter)
        if table_code:
            doc.append(NoEscape(table_code))
            table_counter += 1

        doc.append(Command("newpage"))

    # ---------------------------
    # References
    # ---------------------------
    bib_entries = generate_bibtex(topic, references)
    bib_file = f"{title}_references.bib"
    with open(bib_file, "w", encoding="utf-8") as f:
        f.write("\n\n".join(bib_entries))
    generated_files.append(bib_file)

    doc.append(NoEscape(r"\bibliographystyle{apalike}"))
    doc.append(NoEscape(rf"\bibliography{{{title}_references}}"))

    # ---------------------------
    # Save LaTeX File
    # ---------------------------
    os.makedirs("tex", exist_ok=True)
    tex_file = os.path.join("tex", f"{title}.tex")
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(doc.dumps())
    generated_files.append(tex_file)

    return generated_files
