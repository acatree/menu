import requests
from gtts import gTTS
import subprocess
from openai import OpenAI
import imageio_ffmpeg as ffmpeg
from mutagen.mp3 import MP3

# 1️⃣ 스크립트 생성
def generate_script(api_key, topic):
    client = OpenAI(api_key=api_key)    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"'{topic}'에 대해 한국어로 1분 길이의 흥미로운 스크립트를 작성하세요."}
        ],
        max_completion_tokens=250
    )
    return response.choices[0].message.content.strip()

# 2️⃣ 텍스트 → MP3 변환
def script_to_mp3(script, filename="output.mp3"):
    tts = gTTS(text=script, lang='ko')
    tts.save(filename)
    return filename

# 3️⃣ MP3 → WAV 변환 (CBR로 고정)
def convert_audio_to_wav(input_file, output_file="output.wav"):
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()
    subprocess.run([
        ffmpeg_path, "-y", "-i", input_file,
        "-ar", "44100", "-ac", "2", "-b:a", "192k",
        output_file
    ], check=True)
    return output_file

# 4️⃣ 오디오 길이 계산
def get_audio_duration(filename):
    audio = MP3(filename)
    return audio.info.length

# 5️⃣ 이미지 생성
def generate_images(api_key, topic, count=5):
    client = OpenAI(api_key=api_key)
    image_files = []

    for i in range(count): 
        prompt = (
            f"{topic}에 관한 스크립트 내용을 요약 및 시각적으로 표현한 장면, "
            f"직접적인 인물 이름이나 브랜드 대신 묘사적/추상적 스타일 사용, "
            f"variation {i+1}"
        )
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024"
        )
        image_url = response.data[0].url if response.data and response.data[0].url else None
        if not image_url:
            raise ValueError("❌ 이미지 URL을 생성하지 못했습니다.")
        img_data = requests.get(image_url).content
        filename = f"image_{i+1}.png"
        with open(filename, 'wb') as f:
            f.write(img_data)
        image_files.append(filename)

    return image_files

# 6️⃣ 비디오 생성
def create_video(images, audio_file, output_file="output.mp4"):
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()

    # 오디오를 WAV로 변환
    fixed_audio = convert_audio_to_wav(audio_file)

    # 오디오 길이 확인
    audio_length = get_audio_duration(audio_file)
    num_images = len(images)
    duration_per_image = audio_length / num_images

    # 이미지 목록 파일 생성
    with open("images.txt", "w", encoding="utf-8") as f:
        for img in images[:-1]:
            f.write(f"file '{img}'\n")
            f.write(f"duration {duration_per_image}\n")
        # 마지막 이미지는 duration 없이 반복 → ffmpeg가 자연스럽게 오디오 끝까지 유지
        f.write(f"file '{images[-1]}'\n")

    # ffmpeg 실행
    subprocess.run([
        ffmpeg_path, "-y", "-f", "concat", "-safe", "0",
        "-i", "images.txt", "-i", fixed_audio,
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        output_file
    ], check=True)

    return output_file


# 7️⃣ 최종 함수
def create_youtube_short(api_key, topic, num_images=5):
    script = generate_script(api_key, topic)
    audio_file = script_to_mp3(script, "output.mp3")
    images = generate_images(api_key, topic, count=num_images)
    video_file = create_video(images, audio_file, "output.mp4")
    return video_file
