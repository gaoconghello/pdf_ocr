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

# api_key= os.getenv("OPENAI_API_KEY")

client = OpenAI(
    base_url=base_url,
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
        model="google/gemini-2.5-pro-preview",
        # model="deepseek/deepseek-r1:free",
        # model="gpt-4o-mini",
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


def save_to_markdown(content, output_file, text_content=None):
    """将内容保存到markdown文件

    Args:
        content: 要保存的内容
        output_file: 输出文件路径
        text_content: 原文内容，默认为None
    """
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 如果有原文内容，添加到保存内容中
    if text_content:
        final_content = f"{content}\n\n### 原文\n\n{text_content}\n"
    else:
        final_content = content
        
    # 保存内容到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
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
    ## 硬性规则

    1. **最终输出仅含**“第一部分：评分环节”和“第二部分：详细点评”两大段落。
    2. **不得出现**开场白、结束语或任何超出规定段落的文字。
    3. “第二部分”每条点评 **28–32 个汉字**；若无可评请写“无”。
    4. “第二部分”语言形式评价,可突破字数限制，列出错误和正确的内容，每一个错误和改正为一行 满足markdown语法，格式参考：“used to exercise” → 应为 “as exercise” 或 “to exercise”。
    5. 语气**温和、像老师**，既肯定优点，又指出改进方向。
    6. **严控高分**，同等水平优先给较低分。
    7. 返回严格遵守markdown语法，一：评分环节和二：详细点评 开头加入 ### ，满足markdown语法。

    ---

    ## 角色定位

    你是一名经验丰富、语气亲切的中小学英语老师。

    ---

    ## 任务说明

    阅读学生作文，依下列标准打分并写出建设性点评。

    ---

    ### 一：评分环节（总分 15 分）

    | 维度           | 说明                     | 分值 |
    | -------------- | ------------------------ | ---- |
    | 任务完成与内容 | 主题完整度、信息充实程度 | 0–5  |
    | 结构与连贯性   | 段落安排、过渡自然程度   | 0–5  |
    | 语言能力       | 词汇多样性、语法准确性   | 0–5  |
    | **总得分**     | 三项之和                 | 0–15 |

    > **输出格式（示例）**
    > - 任务完成与内容：3
    > - 结构与连贯性：2
    > - 语言能力：2
    > - **总得分：7**

    ---

    ### 二：详细点评

    > **格式要求**
    >
    > - 依 1–5 大项顺序；子项以 “- ” 开头，符合 Markdown 段落语法。
    > - **每行 28–32 汉字**；句末不加标点。
    > - 若某项确无可评写“无”。

    1. **总体评价**

    - 主题聚焦度、首尾呼应及段落服务主题情况

    2. **内容评价**

    - 中心思想、论据支持、逻辑条理与说服力

    3. **素材利用评价**

    - 课文借鉴、观点引用及时态运用情况

    4. **结构评价**

    - 三段式完整度、衔接词使用与层次清晰度，点评涉及原文，请使用原文的英文，不要进行中文翻译

    5. **语言形式评价**

    - 语法拼写错误、词汇多样性与表达精准度

    ---

    **待批改作文：**

    ```text
    {{text_content}}
    ```

    """

    try:
        # 读取文本文件内容
        text_content = read_text_file(text_file_path)
        
        # 使用format方法格式化prompt
        formatted_prompt = prompt.format(text_content=text_content)

        # 使用LLM分析文本内容
        result = analyze_text(text_content, formatted_prompt)
        
        # 如果指定了输出文件，则保存结果
        if output_file:
            save_to_markdown(result, output_file, text_content)

        return result

    except Exception as e:
        error_message = f"处理文件时出错: {e}"
        print(error_message)
        return error_message


if __name__ == "__main__":
    # 直接设置文本文件路径变量
    text_file_path = "output/example_page_12_text.txt"  # 在这里直接修改文件路径
    
    # 设置输出文件路径
    output_file = "output/example_page_12_text.md"
    
    # 调用函数进行点评和评分，并保存结果
    result = score_and_comment(text_file_path, output_file)
    
    # 输出结果
    print(result)
