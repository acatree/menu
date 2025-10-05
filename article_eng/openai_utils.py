import openai
def ask_question(question, language="ko", api_key=None):
    if api_key:
        import openai
        openai.api_key = api_key

    # 프롬프트 구체화
    if language == "ko":
        system_prompt = (
            "당신은 SCI/KCI 수준의 학술 논문 작성 전문가입니다. "
            "주어진 주제에 대해 다음 사항을 지켜 작성하세요:\n"
            "1. 전문적이고 학술적인 어휘 사용\n"
            "2. 정확한 문장 구조와 논리적 흐름\n"
            "3. 초록, 서론, 관련 연구, 분석, 결론 등 각각의 섹션에 맞는 문체 적용\n"
            "4. 요구된 글자 수 또는 단어 수 준수\n"
            "5. 명확하고 중립적인 기술 방식 유지"
        )
    else:
        system_prompt = (
            "You are an expert in academic paper writing at SCI/KCI level. "
            "Follow these rules:\n"
            "1. Use professional, academic vocabulary.\n"
            "2. Maintain logical structure and coherent flow.\n"
            "3. Adapt style for each section (abstract, introduction, related work, methods, analysis, conclusion).\n"
            "4. Respect requested word/length limits.\n"
            "5. Keep writing neutral, clear, and precise."
        )

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_completion_tokens=3000
    )
    return response.choices[0].message.content.strip()
