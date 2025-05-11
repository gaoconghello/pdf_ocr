# PDF OCR 识别工具

## 项目介绍

这是一个用于处理PDF扫描件的OCR识别工具，可以将PDF文件转换为图片，并使用AI模型进行文字识别。特别适合处理包含手写内容的PDF文档，如批改过的作业等。

## 功能特点

- 将PDF文件转换为高质量图片
- 支持选择性处理PDF的特定页面
- 使用先进的AI模型进行OCR文字识别
- 可自定义OCR识别提示，优化识别效果
- 支持保存单页PDF文件
- 可配置输出图片格式和分辨率
- 自动保存识别结果为文本文件
- 支持对英文作文进行AI打分和详细点评

## 安装说明

### 环境要求

- Python 3.10+
- 依赖包：详见 requirements.txt

### 安装步骤

1. 克隆或下载本项目

2. 创建并激活虚拟环境（推荐）
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/MacOS
   source venv/bin/activate
   ```

3. 安装依赖包
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量
   - 复制 `env_example` 文件为 `.env`
   - 在 `.env` 文件中设置您的 API 密钥和基础 URL
   ```
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_BASE_URL=your_base_url_here
   ```

## 使用方法

### 基本用法

```bash
# 处理整个 PDF 文件
python main.py example.pdf
```

### 指定页码范围

```bash
# 只处理第 3 页到第 5 页
python main.py example.pdf -s 3 -e 5
```

### 自定义输出设置

```bash
# 自定义输出目录和图片格式
python main.py example.pdf -o custom_output -f jpg
```

### 保存单页PDF和自定义OCR提示

```bash
# 保存单页 PDF 并使用自定义 OCR 提示
python main.py example.pdf -p --prompt "请识别图片中的所有文字内容"
```

### 英文作文打分和点评

```bash
# 对OCR识别后的文本文件进行英文作文打分和点评
python score_and_comment.py output/example_text.txt

# 指定输出文件路径
python score_and_comment.py output/example_text.txt -o output/example_score.md
```

### 命令行参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `pdf_path` | - | PDF文件路径（必需） | - |
| `--start` | `-s` | 起始页码 | 1 |
| `--end` | `-e` | 结束页码 | PDF最后一页 |
| `--output` | `-o` | 输出目录 | output |
| `--dpi` | `-d` | 图片DPI（分辨率） | 300 |
| `--format` | `-f` | 图片格式 | png |
| `--save-pdf` | `-p` | 是否保存单页PDF | False |
| `--prompt` | - | 自定义OCR识别提示文本 | 默认提示 |

### 英文作文打分参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `text_file_path` | - | 文本文件路径（必需） | - |
| `--output` | `-o` | 输出文件路径 | None（仅打印结果） |

## 默认OCR提示

如果不指定自定义提示，系统将使用以下默认提示进行OCR识别：

```
请分析这张图片中的手写文字内容:
- 因为是批改的作业，英文会有错，原文输出即可,无需解释性的语言，
- 如果识别出文字是已经被黑色笔画划掉的，则不输出对应的单词，
- 如果为红色笔画，则忽略笔画，此笔画为批注内容，可以当作不存在红色笔画，
```

## 英文作文打分标准

系统使用以下标准对英文作文进行评分和点评：

### 评分维度（总分15分）

- **任务完成与内容**（0-5分）：主题完整度、信息充实程度
- **结构与连贯性**（0-5分）：段落安排、过渡自然程度
- **语言能力**（0-5分）：词汇多样性、语法准确性

### 详细点评内容

- **总体评价**：主题聚焦度、首尾呼应及段落服务主题情况
- **内容评价**：中心思想、论据支持、逻辑条理与说服力
- **素材利用评价**：课文借鉴、观点引用及时态运用情况
- **结构评价**：三段式完整度、衔接词使用与层次清晰度
- **语言形式评价**：语法拼写错误、词汇多样性与表达精准度

## 项目结构

- `main.py` - 主程序入口
- `pdf_to_img.py` - PDF转图片功能模块
- `pdf_to_txt.py` - 图片OCR识别功能模块
- `score_and_comment.py` - 英文作文打分和点评功能模块
- `requirements.txt` - 项目依赖列表
