import openai

def ask_question(question, language="ko", api_key=None):
    if api_key:
        openai.api_key = api_key
    system_prompt = "당신은 SCI/KCI 수준 학술 논문 작성 전문가입니다." if language=="ko" else "You are an expert in academic paper writing."
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
