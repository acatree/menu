import os
import io
import requests
import contextlib
import matplotlib.pyplot as plt
import openai
from openai import OpenAI
from pylatex import Document, Command, NoEscape

openai.api_key = None  # Flask 또는 환경 변수에서 설정

# ---------------------------
# ChatGPT 질의 함수
# ---------------------------
def 질문_요청(질문, 언어="ko"):
    시스템_프롬프트 = "당신은 SCI/KCI 수준의 한국어 학술 논문 작성 전문가입니다."
    응답 = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": 시스템_프롬프트},
            {"role": "user", "content": 질문}
        ],
        temperature=0.7,
