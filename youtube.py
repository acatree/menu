import openai
openai.api_key = 
openai.api_key = "[your_opne_ai_api_token]"
def generate_script():
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt="[만들고 싶은 내용을 적으세요. 예) Generate a one-minute paragraph about technology trends.]",
        max_tokens=150
    )
    return response.choices[0].text.strip()

script = generate_script()
print(script)


from gtts import gTTS

def script_to_mp3(script, filename):
    tts = gTTS(text=script, lang='en')
    tts.save(filename)
    print(f'Audio content written to file {filename}')

script_to_mp3(script, 'output.mp3')


import openai

def generate_image(prompt, filename):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response['data'][0]['url']
    # Download the image
    import requests
    img_data = requests.get(image_url).content
    with open(filename, 'wb') as handler:
        handler.write(img_data)
    print(f'Image saved to {filename}')
generate_image("[만들고 싶은 이미지 설명을 적으세요. 예) A futuristic depiction of technology trends]", "cover_image.png")

ffmpeg -loop 1 -i cover_image.png -i output.mp3 -c:v libx264 -c:a aac -b:a 192k -shortest output.mp4
