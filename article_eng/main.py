import sys, os
sys.path.append(os.path.dirname(__file__))
from pylatex import Document, Command, NoEscape, Package
import os, re
from . import openai_utils
from . import text_utils
from . import figure_utils
from . import bib_utils

def generate_real_estate_paper(topic, authors=None, affiliations=None, emails=None, api_key=None):
    """
    Generate a professional real estate / economics academic paper in LaTeX
    - scrartcl based
    - authors, affiliations, emails included
    - regression tables and graphs formatted professionally
    """

    # 1. Creative research title
    creative_title = openai_utils.ask_question(
        f"Generate a novel and creative research paper title related to real estate or economics for '{topic}'. Remove quotation marks.",
        api_key=api_key
    ).strip().replace('"', '').replace("'", "")

    research_topic = openai_utils.ask_question(
        f"Summarize the research topic for '{creative_title}' in 1-2 sentences in the context of real estate/economics.",
        api_key=api_key
    )

    # 2. LaTeX setup
    doc = Document(documentclass='scrartcl', document_options=['11pt', 'a4paper'])
    doc.packages.extend([
        Package('geometry', options=['margin=1in']),
        Package('graphicx'),
        Package('amsmath'),
        Package('amssymb'),
        Package('siunitx'),
        Package('hyperref', options='colorlinks=true, linkcolor=blue, citecolor=blue, urlcolor=blue'),
        Package('caption', options='font=small,labelfont=bf'),
        Package('booktabs'),
        Package('setspace'),
        Package('titlesec'),
        Package('float'),
        Package('kotex')
    ])
    doc.append(NoEscape(r'\titleformat{\section}{\Large\bfseries}{\thesection}{1em}{}'))
    doc.append(NoEscape(r'\titleformat{\subsection}{\large\bfseries}{\thesubsection}{0.75em}{}'))
    doc.append(NoEscape(r'\titleformat{\subsubsection}{\normalsize\bfseries}{\thesubsubsection}{0.5em}{}'))
    doc.append(NoEscape(r'\onehalfspacing'))

    # 3. Authors / Affiliations / Emails
    if authors is None: authors = ["Sangkyu Kang"]
    if affiliations is None: affiliations = ["Department of Economics, Korea University, Seoul, Korea"]
    if emails is None: emails = ["sangkyu@example.com"]

    author_texts = [f"{a}\\thanks{{{aff}. Email: {em}}}" for a, aff, em in zip(authors, affiliations, emails)]
    doc.preamble.append(NoEscape(r'\title{\Large\bfseries ' + creative_title + '}'))
    doc.preamble.append(NoEscape(r'\author{' + " \\\\ ".join(author_texts) + '}'))
    doc.preamble.append(NoEscape(r'\date{}'))
    doc.append(NoEscape(r'\maketitle'))

    # 4. Abstract / Keywords
    doc.append(NoEscape(r'\begin{abstract}'))
    abstract_text = openai_utils.ask_question(
        f"Write a 180-220 word abstract for a real estate/economics paper on '{research_topic}'",
        api_key=api_key
    )
    doc.append(NoEscape(text_utils.clean_section_text(abstract_text)))
    doc.append(NoEscape(r'\end{abstract}'))
    doc.append(NoEscape(r'\textbf{Keywords:} ' + text_utils.extract_keywords(abstract_text, api_key=api_key)))
    doc.append(Command('newpage'))

    # 5. Bibliography
    bib_entries = bib_utils.generate_bibtex(research_topic, 10, api_key=api_key)
    with open("references.bib", 'w', encoding='utf-8') as f:
        f.write("\n\n".join(bib_entries))
    bib_keys = [re.search(r'@.*?\{(.*?),', e).group(1) for e in bib_entries if re.search(r'@.*?\{(.*?),', e)]

    # 6. Sections
    section_requirements = {
        "Introduction": 300,
        "Literature Review": 350,
        "Data & Methodology": 300,
        "Results": 600,
        "Discussion": 300,
        "Conclusion": 250
    }
    sections = ["Introduction", "Literature Review", "Data & Methodology", "Results", "Discussion", "Conclusion"]

    for sec in sections:
        doc.append(NoEscape(f"\\section{{{sec}}}"))
        min_words = section_requirements.get(sec, 300)

        if sec == "Results":
            import pandas as pd, numpy as np
            local_env = {"pd": pd, "np": np}
            df = None

            # Generate example dataset
            data_prompt = (
                f"Generate example real estate or economic dataset for '{creative_title}' "
                "as a pandas DataFrame named 'df', 5-6 columns, 20-30 rows, with numeric variables suitable for regression analysis."
            )
            data_code = openai_utils.ask_question(data_prompt, api_key=api_key)
            try:
                if "df" not in data_code:
                    data_code = f"import pandas as pd\nimport numpy as np\ndf = {data_code}"
                exec(data_code, local_env)
                df = local_env.get("df", None)
            except Exception:
                df = pd.DataFrame({
                    "Price": np.random.rand(20)*500000 + 50000,
                    "Size": np.random.randint(50, 200, 20),
                    "Bedrooms": np.random.randint(1,5,20),
                    "DistanceToCenter": np.random.rand(20)*20,
                    "Income": np.random.randint(2000, 8000, 20)
                })

            # Results text
            analysis_prompt = (
                f"Write the '{sec}' section for '{creative_title}' using df data. "
                f"Include descriptive statistics, regression analysis, and interpretation. Minimum {min_words} words."
            )
            text_exp = openai_utils.ask_question(analysis_prompt, api_key=api_key)
            text = text_utils.clean_section_text(text_exp)
            doc.append(NoEscape(text))

            # Graph
            try:
                fig = figure_utils.generate_graph_from_df(sec, df, creative_title)
                if fig:
                    figure_utils.insert_figure(doc, fig, f"{sec} Figure", placement='H')
            except Exception as e:
                print(f"[Graph generation failed: {e}]")

            # Table
            try:
                table_latex = df.to_latex(index=False, longtable=False, caption=f"{sec} Table", label=f"tab:{sec}")
                doc.append(NoEscape(r"\begin{table}[H]\centering" + table_latex + r"\end{table}"))
            except Exception as e:
                print(f"[Table generation failed: {e}]")

        else:
            # Other sections
            text_exp = openai_utils.ask_question(
                f"Write the '{sec}' section for '{creative_title}', minimum {min_words} words, in real estate/economics context.",
                api_key=api_key
            )
            text = text_utils.clean_section_text(text_exp, remove_title=True, section_title=sec)
            text = text_utils.insert_cites(text, bib_keys)
            doc.append(NoEscape(text))

        doc.append(Command('newpage'))

    # 7. Bibliography
    doc.append(NoEscape(r"\bibliographystyle{apalike}"))
    doc.append(NoEscape(r"\bibliography{references}"))

    # 8. Save and collect assets
    tex_file = "main.tex"
    doc.generate_tex(tex_file.replace(".tex", ""))

    asset_files = []
    for folder in ["images", "graphs"]:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                asset_files.append(os.path.join(folder, file))

    return tex_file, "references.bib", asset_files, creative_title, research_topic


