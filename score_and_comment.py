from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 从环境变量获取API密钥和基础URL
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY 未在环境变量中设置")

base_url = os.getenv("OPENROUTER_BASE_URL")
if not base_url:
    raise ValueError("OPENROUTER_BASE_URL 未在环境变量中设置")

api_key= os.getenv("OPENAI_API_KEY")

client = OpenAI(
    # base_url=base_url,
    api_key=api_key,
)


def analyze_text(text_content, prompt):
    """使用LLM分析文本内容

    Args:
        text_content: 要分析的文本内容
        prompt: 提示文本

    Returns:
        str: 分析后的文本内容
    """
    content = [
        {
            "type": "text",
            "text": f"{prompt}\n\n{text_content}"
        }
    ]

    completion = client.chat.completions.create(
        # model="google/gemini-2.5-pro-preview",
        # model="deepseek/deepseek-r1:free",
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": content
            }
        ]
    )

    return completion.choices[0].message.content


def read_text_file(file_path):
    """读取文本文件内容

    Args:
        file_path: 文本文件路径

    Returns:
        str: 文件内容
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def save_to_markdown(content, output_file):
    """将内容保存到markdown文件

    Args:
        content: 要保存的内容
        output_file: 输出文件路径
    """
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 保存内容到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"结果已保存到: {output_file}")


def score_and_comment(text_file_path, output_file=None):
    """对英文作文进行点评和评分

    Args:
        text_file_path: 文本文件路径
        output_file: 输出文件路径，默认为None

    Returns:
        str: 点评和评分结果
    """
    # 评分和点评的提示词
    prompt = """
    Please help polish and improve the following English composition written by a middle school student. The task includes the following steps:

    1. First, correct all grammatical and word usage errors.
    2. Then, enhance sentence variety and overall fluency.
    3. Next, provide a one-sentence comment on the composition’s strengths or weaknesses.
    4. Finally, give a score out of 15 based on the Chinese middle school English writing standards, using the following three subcategories (each out of 5):

        - (a) Task Completion & Content (5 points)
        - (b) Organization & Coherence (5 points)
        - (c) Language (Grammar, Vocabulary, Sentence Structure) (5 points)
        - Please show the subtotal for each category, and ensure that the final score is the sum of the three (max 15).

    Scoring criteria:

        -Only compositions that use advanced sentence structures such as attributive clauses, adverbial clauses, and complex linking words, with clear logical coherence, can be awarded full marks.
        -Be strict and avoid giving high scores unless all criteria are clearly met.

    5. Do not include any additional descriptive language or introductory phrases—only the revised composition, the one-sentence comment, and the score.

    output xample：
    ### 1. Corrected Version (Grammar and Word Usage):

    Dear Mary,

    I heard about your situation yesterday, but I'm so sorry I couldn't come to look after you. Here is some advice for you to get healthy.

    First, you should have a good rest; that is good for your body. Then, you should eat more fruit and vegetables. They are good for your health. Next, you need to do more sports (or: get more exercise). Finally, it's important that you should follow the doctor's advice.

    I hope you can get healthy soon.

    Peng Ruixuan

    ---

    ### 2. Enhanced Version (Sentence Variety and Fluency):

    Dear Mary,

    I was sorry to hear you were unwell yesterday, and I regret that I couldn't visit you. However, I'd like to offer some advice that might help you recover and feel better.

    Firstly, ensuring you get plenty of rest is crucial, as this will allow your body to heal. Secondly, it would be beneficial to eat more fruits and vegetables, because they are rich in vitamins and essential for good health. In addition, once you feel a bit stronger, engaging in some light exercise can also be helpful. Most importantly, please make sure you carefully follow all the instructions and advice given by your doctor.

    I sincerely hope you get well soon and are back on your feet quickly.

    Warmly,
    Peng Ruixuan

    ---

    ### 3. One-sentence comment on the composition's strengths or weaknesses:

    The original composition shows a kind intention and a basic attempt at logical structure, but it is significantly impaired by numerous fundamental errors in grammar, spelling, and word choice.   

    ---

    ### 4. Score out of 15:

    **Score: 6**

    **Reasoning for the score (based on the *original* submission against Chinese middle school English writing standards):**
    -   **Task Completion & Content (score:2):** The student understood the task of writing to a sick friend and giving advice. The advice itself is relevant (rest, food, exercise, doctor's orders).     
    -   **Organization & Coherence (score:2.5):** The use of "First," "Then," "Next," "Finally" shows an attempt at logical organization, which is commendable at this level.
    -   **Language (Grammar, Vocabulary, Sentence Structure) (score:1.5):** This is the weakest area.
        -   **Grammar:** Multiple significant errors (e.g., "I you was situation," "can't to look," "You're shaild").
        -   **Vocabulary/Word Choice:** Incorrect word forms ("advises" instead of "advice," "healthy" as a noun instead of "health") and awkward phrasing ("make healthy," "make more sports," "healthy early").
        -   **Sentence Structure:** Sentences are very basic and often grammatically flawed. There are no advanced structures like attributive clauses, adverbial clauses, or complex linking words used correctly. Fluency is poor due to the errors.

    The score is kept low because of the high density of basic errors and the lack of advanced sentence structures required for higher marks according to the criteria. While the intent is good and there's an attempt at organization, the linguistic execution is far below the standard for achieving
    even a moderate score under strict marking.    
    """

    try:
        # 读取文本文件内容
        text_content = read_text_file(text_file_path)

        # 使用LLM分析文本内容
        result = analyze_text(text_content, prompt)
        
        # 如果指定了输出文件，则保存结果
        if output_file:
            save_to_markdown(result, output_file)

        return result

    except Exception as e:
        error_message = f"处理文件时出错: {e}"
        print(error_message)
        return error_message


if __name__ == "__main__":
    # 直接设置文本文件路径变量
    text_file_path = "output/example_page_4_text.txt"  # 在这里直接修改文件路径
    
    # 设置输出文件路径
    output_file = "output/example_page_4_score_and_comment.md"
    
    # 调用函数进行点评和评分，并保存结果
    result = score_and_comment(text_file_path, output_file)
    
    # 输出结果
    print(result)
