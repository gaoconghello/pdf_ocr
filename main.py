import os
import argparse
from pdf_to_img import pdf_to_image
from pdf_to_txt import analyze_image, save_to_file, extract_chinese_name
from PyPDF2 import PdfReader
from score_and_comment import score_and_comment
from md_to_doxc import convert_md_to_docx


def process_pdf_page(pdf_path, page_number, output_dir='output', dpi=300, fmt='png', save_pdf=False, prompt=None, pages_per_image=1):
    """
    处理PDF的单页：转换为图片并进行OCR识别
    
    Args:
        pdf_path: PDF文件路径
        page_number: 需要处理的页码（从1开始）
        output_dir: 输出目录
        dpi: 图片DPI
        fmt: 图片格式
        save_pdf: 是否保存单页PDF
        prompt: OCR识别提示文本，如果为None则使用默认提示
    
    Returns:
        dict: 包含处理结果的字典
    """
    # 默认OCR提示文本
    if prompt is None:
        prompt = """
        请分析这张图片中的手写文字内容:
        - 因为是批改的作业，英文会有错，原文输出即可,无需解释性的语言，
        - 如果识别出文字是已经被黑色笔画划掉的，则不输出对应的单词，
        - 如果为红色笔画，则忽略笔画，此笔画为批注内容，可以当作不存在红色笔画，
        - 在最上方会有手写的中文，这是手写文字的姓名，请识别后，放入输出内容中的第一行，其他识别内容从第二行开始输出。        
        """
    
    try:
        # 步骤1：将PDF转换为图片
        if pages_per_image > 1:
            print(f"正在处理第 {page_number} 至 {page_number + pages_per_image - 1} 页...")
        else:
            print(f"正在处理第 {page_number} 页...")
        img_result = pdf_to_image(pdf_path, page_number, output_dir, dpi, fmt, save_pdf, pages_per_image)
        image_path = img_result['image_path']
        print(f"图片已保存至: {image_path}")
        
        # 步骤2：OCR识别图片内容
        print(f"正在进行OCR识别...")
        ocr_text = analyze_image(image_path, prompt)
        
        # 提取中文姓名
        # chinese_name = extract_chinese_name(ocr_text)
        # name_suffix = f"_{chinese_name}" if chinese_name else ""
        # TODO 暂时不加入姓名
        name_suffix = ""
        
        # 步骤3：保存OCR结果到文本文件
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}_text{name_suffix}.txt")
        saved_path = save_to_file(ocr_text, output_file)
        print(f"文本已保存至: {saved_path}")
        
        # 步骤4：对提取的文本进行评分和点评
        print(f"正在进行评分和点评...")
        score_output_file = os.path.join(output_dir, f"{base_name}_score{name_suffix}.md")
        score_result = score_and_comment(saved_path, score_output_file)
        print(f"评分和点评已保存至: {score_output_file}")
        
        # 步骤5：将MD文档转换为Word文档
        chinese_name = extract_chinese_name(ocr_text)
        name_suffix = f"_{chinese_name}" if chinese_name else ""

        print(f"正在将MD文档转换为Word文档...")
        docx_output_file = os.path.join(output_dir, f"{base_name}_score{name_suffix}.docx")
        docx_path = convert_md_to_docx(score_output_file, docx_output_file)
        print(f"Word文档已保存至: {docx_path}")
        
        return {
            "image_path": image_path,
            "text_path": saved_path,
            "score_path": score_output_file,
            "docx_path": docx_path,
            "pdf_path": img_result.get("pdf_path"),
            "success": True
        }
    
    except Exception as e:
        print(f"处理第 {page_number} 页时出错: {e}")
        return {"success": False, "error": str(e), "page_number": page_number}


def get_pdf_page_count(pdf_path):
    """
    获取PDF文件的总页数
    
    Args:
        pdf_path: PDF文件路径
    
    Returns:
        int: PDF文件的总页数
    """
    try:
        pdf_reader = PdfReader(pdf_path)
        return len(pdf_reader.pages)
    except Exception as e:
        raise ValueError(f"无法读取PDF文件: {e}")


def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="PDF OCR处理工具")
    parser.add_argument("pdf_path", help="PDF文件路径")
    parser.add_argument("-s", "--start", type=int, default=1, help="起始页码（从1开始，默认为1）")
    parser.add_argument("-e", "--end", type=int, help="结束页码（默认为PDF的最后一页）")
    parser.add_argument("-o", "--output", default="output", help="输出目录（默认为'output'）")
    parser.add_argument("-d", "--dpi", type=int, default=300, help="图片DPI（默认为300）")
    parser.add_argument("-f", "--format", default="png", help="图片格式（默认为'png'）")
    parser.add_argument("-p", "--save-pdf", action="store_true", help="是否保存单页PDF（默认不保存）")
    parser.add_argument("--prompt", help="自定义OCR识别提示文本")
    parser.add_argument("--pages", type=int, default=1, help="每张图片包含的PDF页数，默认为1")
    
    args = parser.parse_args()
    
    # 检查PDF文件是否存在
    if not os.path.exists(args.pdf_path):
        print(f"错误: PDF文件 '{args.pdf_path}' 不存在")
        return
    
    # 获取PDF总页数
    total_pages = get_pdf_page_count(args.pdf_path)
    print(f"PDF文件共有 {total_pages} 页")
    
    # 确定处理的页码范围
    start_page = max(1, args.start)  # 确保起始页码至少为1
    end_page = args.end if args.end else total_pages  # 如果未指定结束页码，则处理到最后一页
    
    # 确保页码范围有效
    if start_page > total_pages:
        print(f"错误: 起始页码 {start_page} 超出PDF总页数 {total_pages}")
        return
    
    if end_page > total_pages:
        print(f"警告: 结束页码 {end_page} 超出PDF总页数 {total_pages}，将处理到最后一页")
        end_page = total_pages
    
    # 确保输出目录存在
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # 处理PDF页面
    results = []
    failed_pages = []
    
    # 根据pages_per_image参数调整循环步长，确保每次处理指定数量的页面
    for page_num in range(start_page, end_page + 1, args.pages):
        # 第一次尝试处理
        result = process_pdf_page(
            args.pdf_path, 
            page_num, 
            args.output, 
            args.dpi, 
            args.format, 
            args.save_pdf,
            args.prompt,
            args.pages
        )
        
        # 如果失败，进行一次重试
        if not result.get("success", False):
            print(f"第 {page_num} 页处理失败，正在进行重试...")
            result = process_pdf_page(
                args.pdf_path, 
                page_num, 
                args.output, 
                args.dpi, 
                args.format, 
                args.save_pdf,
                args.prompt,
                args.pages
            )
            
            # 如果重试后仍然失败，记录失败页码
            if not result.get("success", False):
                failed_pages.append(page_num)
                print(f"第 {page_num} 页重试后仍然失败")
        
        results.append(result)
    
    # 打印处理结果统计
    success_count = sum(1 for r in results if r.get("success", False))
    print(f"\n处理完成: 共处理 {len(results)} 页，成功 {success_count} 页，失败 {len(results) - success_count} 页")
    
    # 如果有失败的页码，输出详细信息
    if failed_pages:
        print("\n以下页码处理失败:")
        for page in failed_pages:
            print(f"- 第 {page} 页")


if __name__ == "__main__":
    main()