import pandas as pd
import os, requests, io, contextlib, traceback
import matplotlib.pyplot as plt
from pylatex import NoEscape
from openai_utils import ask_question

# -----------------------------
# Safe filename for sections
# -----------------------------
def safe_filename(section_title, suffix):
    mapping = {
        "Introduction": "intro",
        "Literature Review": "literature",
        "Data & Methodology": "methods",
        "Results": "results",
        "Discussion": "discussion",
        "Conclusion": "conclusion"
    }
    name = mapping.get(section_title, ''.join(filter(str.isalnum, section_title)))
    return f"{name}_{suffix}.png"

# -----------------------------
# Image generation using OpenAI
# -----------------------------
def generate_images(api_key, topic, section_title, count=1):
    import openai
    openai.api_key = api_key
    os.makedirs("images", exist_ok=True)
    image_files = []

    for i in range(count):
        prompt = (
            f"Generate a professional academic-style figure for the '{section_title}' section "
            f"of a real estate/economics paper titled '{topic}'. "
            "Do not include any brand names or real persons, focus on abstract or illustrative visualization."
        )
        response = openai.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024")
        url = response.data[0].url
        img_data = requests.get(url).content
        filename = os.path.join("images", safe_filename(section_title, f"img{i+1}"))
        with open(filename, 'wb') as f:
            f.write(img_data)
        image_files.append(filename)

    return image_files

# -----------------------------
# Matplotlib figure generation
# -----------------------------
def generate_graph(section_title, topic, figure_number=1, language="en", api_key=None):
    import numpy as np
    os.makedirs("graphs", exist_ok=True)
    fig_path = os.path.join("graphs", safe_filename(section_title, f"fig{figure_number}"))

    prompt = f"""
    Generate self-contained Python matplotlib code for the '{section_title}' section 
    of a real estate/economics paper titled '{topic}'.
    - Include data generation (e.g., x = [1,2,3], y = [4,5,6])
    - Use plt.figure() and plt.savefig(r'{fig_path}') to save the figure
    - Import necessary libraries (numpy as np)
    - Return only Python code, no explanations or comments
    """

    code = ask_question(prompt, language=language, api_key=api_key)

    try:
        local_env = {"plt": plt, "np": np}
        with contextlib.redirect_stdout(io.StringIO()):  # suppress output
            exec(code, local_env)
        plt.close('all')
    except Exception as e:
        print(f"[Graph generation failed] {section_title}: {e}")
        traceback.print_exc()
        return ""
    return fig_path

# -----------------------------
# LaTeX figure insertion
# -----------------------------
def insert_figure(doc, file_path, caption_text):
    doc.append(NoEscape(r"\begin{figure}[h]"))
    doc.append(NoEscape(r"\centering"))
    doc.append(NoEscape(f"\includegraphics[width=0.9\\textwidth]{{{file_path}}}"))
    doc.append(NoEscape(f"\caption{{{caption_text}}}"))
    doc.append(NoEscape(r"\end{figure}"))

# -----------------------------
# Generate table for section
# -----------------------------
def generate_table(section_title, topic, api_key=None):
    """
    Generate a simple table for a given section and topic, return LaTeX table code.
    """
    try:
        prompt = (
            f"Create a small dataset for the '{section_title}' section of a real estate/economics paper "
            f"titled '{topic}'. Include 3-5 columns and 5-10 rows, numeric values suitable for analysis. "
            "Output the data in CSV format with clear column names."
        )
        csv_text = ask_question(prompt, language="en", api_key=api_key)

        # Parse CSV
        df = pd.read_csv(io.StringIO(csv_text))

        # Convert to LaTeX table
        latex_table = df.to_latex(index=False, escape=False)
        return latex_table

    except Exception as e:
        print(f"[generate_table error] {e}")
        return None
