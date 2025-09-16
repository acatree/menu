import requests
from gtts import gTTS
import subprocess
import os
from openai import OpenAI

def generate_script(api_key, topic):
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"'{topic}'에 대해 한국어로 2분 길이의 흥미로운 스크립트를 작성하세요."}
        ],
        max_completion_tokens=250  # ✅ 최신 SDK용
    )
    
    # GPT-5-mini는 choices[0].message.content
    return response.choices[0].message.content.strip()

def script_to_mp3(script, filename):
    tts = gTTS(text=script, lang='ko')
    tts.save(filename)
    return filename

def generate_images(api_key, topic, count=5):
    client = OpenAI(api_key=api_key)
    image_files = []

    for i in range(count):
        response = client.images.generate(
            model="gpt-4o-image",  # 최신 이미지 모델
            prompt=f"{topic}, 한국 스타일, 시네마틱 느낌, variation {i+1}",
            size="1024x1024"
        )
        image_url = response.data[0].url
        img_data = requests.get(image_url).content
        filename = f"image_{i+1}.png"
        with open(filename, 'wb') as f:
            f.write(img_data)
        image_files.append(filename)

    return image_files

def create_video(images, audio_file, script, output_file="output.mp4"):
    # 이미지 목록 파일 생성
    with open("images.txt", "w", encoding="utf-8") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write("duration 3\n")
        f.write(f"file '{images[-1]}'\n")  # 마지막 이미지 고정

    # 자막 파일 생성 (SRT)
    with open("subtitles.srt", "w", encoding="utf-8") as srt:
        srt.write("1\n00:00:00,000 --> 00:00:59,000\n")
        srt.write(script + "\n")

    # ffmpeg: 이미지 + 오디오 합성
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "images.txt", "-i", audio_file,
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "temp.mp4"
    ])

    # ffmpeg: 자막 입히기
    subprocess.run([
        "ffmpeg", "-y", "-i", "temp.mp4", "-vf", "subtitles=subtitles.srt",
        "-c:a", "copy", output_file
    ])

    return output_file

def create_youtube_short(api_key, topic, num_images=1):
    script = generate_script(api_key, topic)
    audio_file = script_to_mp3(script, "output.mp3")
    images = generate_images(api_key, topic, count=num_images)
    video_file = create_video(images, audio_file, script, "output.mp4")
    return video_file
