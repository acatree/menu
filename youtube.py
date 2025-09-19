import requests
from gtts import gTTS
import subprocess
from openai import OpenAI
import os
import wave
import imageio_ffmpeg as ffmpeg

def generate_script(api_key, topic):
    client = OpenAI(api_key=api_key)    
    response = client.chat.completions.create(
        #model="gpt-5-mini",
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"'{topic}'에 대해 한국어로 1분 길이의 흥미로운 스크립트를 작성하세요."}
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
        prompt = f"{topic}에 관한 스크립트 내용을 요약 및 시각적으로 표현한 장면, variation {i+1}"
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024"
        )
        # URL 안전 체크
        image_url = response.data[0].url if response.data and response.data[0].url else None
        if not image_url:
            raise ValueError("❌ 이미지 URL을 생성하지 못했습니다. 모델 권한 또는 응답을 확인하세요.")
        # 이미지 저장
        img_data = requests.get(image_url).content
        filename = f"image_{i+1}.png"
        with open(filename, 'wb') as f:
            f.write(img_data)
        image_files.append(filename)

    return image_files

def get_audio_duration(filename):
    """오디오 파일 길이(초) 반환"""
    with wave.open(filename, 'r') as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return duration

def create_video(images, audio_file, script, output_file="output.mp4"):
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()  # 설치된 ffmpeg 경로 반환
    # 1️⃣ 오디오 길이 확인
    audio_length = get_audio_duration(audio_file)
    num_images = len(images)
    duration_per_image = audio_length / num_images

    # 2️⃣ 이미지 목록 파일 생성 (concat용)
    with open("images.txt", "w", encoding="utf-8") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write(f"duration {duration_per_image}\n")
        # 마지막 이미지 반복
        f.write(f"file '{images[-1]}'\n")
        f.write(f"duration {duration_per_image}\n")

    # 3️⃣ 자막 파일 생성 (SRT)
    with open("subtitles.srt", "w", encoding="utf-8") as srt:
        srt.write("1\n00:00:00,000 --> ")
        # SRT 형식: HH:MM:SS,ms
        minutes = int(audio_length // 60)
        seconds = int(audio_length % 60)
        srt.write(f"00:{minutes:02d}:{seconds:02d},000\n")
        srt.write(script + "\n")

    # 4️⃣ ffmpeg: 이미지 + 오디오 합성
    subprocess.run([
        ffmpeg_path, "-y", "-f", "concat", "-safe", "0",
        "-i", "images.txt", "-i", audio_file,
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "temp.mp4"
    ], check=True)

    # 5️⃣ ffmpeg: 자막 입히기 (burn-in)
    subprocess.run([
        ffmpeg_path, "-y", "-i", "temp.mp4", "-vf", "subtitles=subtitles.srt",
        "-c:a", "copy", output_file
    ], check=True)

    return output_file
    
def create_youtube_short(api_key, topic, num_images=1):
    script = generate_script(api_key, topic)
    audio_file = script_to_mp3(script, "output.mp3")
    images = generate_images(api_key, topic, count=num_images)
    video_file = create_video(images, audio_file, script, "output.mp4")
    return video_file
