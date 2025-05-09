from openai import OpenAI
import os
import base64
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 从环境变量获取API密钥
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY 未在环境变量中设置")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=api_key,
)

def encode_image_to_base64(image_path):
    """将本地图片转换为base64编码"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(image_path=None, image_url=None, prompt="What is in this image?"):
    """使用LLM分析图片内容
    
    Args:
        image_path: 本地图片路径
        image_url: 在线图片URL
        prompt: 提示文本
    """
    content = [
        {
            "type": "text",
            "text": prompt
        }
    ]
    
    # 本地图片需要转为base64
    base64_image = encode_image_to_base64(image_path)
    content.append({
        "type": "image_url",
        "image_url": {
            "url": f"data:image/png;base64,{base64_image}"
        }
    })
    
    completion = client.chat.completions.create(
        model="google/gemini-2.5-pro-preview",
        messages=[
            {
                "role": "user",
                "content": content
            }
        ]
    )
    
    return completion.choices[0].message.content

if __name__ == "__main__":
    # 使用本地图片
    local_image_path = "output/example_page_4.png"
    result = analyze_image(
        image_path=local_image_path, 
        prompt="请分析这张图片中的手写文字内容，因为是批改的作业，英文会有错，原文输出即可,无需解释性的语言，如果识别出文字是已经被划掉的，则不输出对应的单词"
    )
    print(result)