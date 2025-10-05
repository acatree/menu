def ask_question(question, language="en", api_key=None):
    """
    Send a request to OpenAI to generate academic-style text.
    Fully English prompts for real estate/economics context.
    Respects section style and word count requirements.
    """
    if api_key:
        import openai
        openai.api_key = api_key

    # System prompt tailored for academic papers in economics/real estate
    system_prompt = (
        "You are an expert academic writer for high-quality economics and real estate journals. "
        "When writing, follow these rules:\n"
        "1. Use professional, formal academic vocabulary.\n"
        "2. Maintain logical structure and coherent flow.\n"
        "3. Adapt style for each section (abstract, introduction, literature review, data & methodology, results, discussion, conclusion).\n"
        "4. Respect requested word or length limits.\n"
        "5. Keep writing clear, neutral, and precise.\n"
        "6. Include quantitative analysis, tables, or graphs references where appropriate."
    )

    import openai
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_tokens=3000
    )

    return response.choices[0].message.content.strip()
