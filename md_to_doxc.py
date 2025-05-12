import markdown
from bs4 import BeautifulSoup
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt

# 设置段落字体为宋体
def set_font_simsun(run):
    run.font.name = '宋体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    run.font.size = Pt(12)

# 1. 读取 Markdown 文件
with open("output/example_page_1_score_and_comment.md", "r", encoding="utf-8") as f:
    md_content = f.read()

# 2. Markdown 转 HTML，再用 BeautifulSoup 解析
html = markdown.markdown(md_content)
soup = BeautifulSoup(html, "html.parser")

# 3. 创建 Word 文档
doc = Document()

# 设置默认样式为宋体
style = doc.styles['Normal']
style.font.name = '宋体'
style._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
style.font.size = Pt(12)

# 4. 转写 HTML 元素到 Word
for element in soup.children:
    if element.name in ['h1', 'h2', 'h3']:
        level = int(element.name[1])
        paragraph = doc.add_heading(element.text, level=level)
        for run in paragraph.runs:
            set_font_simsun(run)
    elif element.name == 'p':
        paragraph = doc.add_paragraph(element.text)
        for run in paragraph.runs:
            set_font_simsun(run)
    elif element.name == 'ul':
        for li in element.find_all("li"):
            paragraph = doc.add_paragraph(li.text, style='ListBullet')
            for run in paragraph.runs:
                set_font_simsun(run)
    elif element.name == 'ol':
        for li in element.find_all("li"):
            paragraph = doc.add_paragraph(li.text, style='ListNumber')
            for run in paragraph.runs:
                set_font_simsun(run)

# 5. 保存 Word 文档
doc.save("output/example_page_1_score_and_comment.docx")
