import os
from pdf2image import convert_from_path
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter


def pdf_to_image(pdf_path, page_number, output_dir='output', dpi=300, fmt='png', save_pdf=False):
    """
    将PDF文件的指定页转换为图片，并可选择保存单页PDF
    
    Args:
        pdf_path: PDF文件路径
        page_number: 需要转换的页码（从1开始）
        output_dir: 输出图片目录
        dpi: 输出图片的DPI（分辨率）
        fmt: 输出图片格式（png, jpg等）
        save_pdf: 是否保存单页PDF文件
    
    Returns:
        字典，包含输出图片路径和可选的PDF路径
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 检查页码有效性
    if page_number < 1:
        raise ValueError("页码必须从1开始")
    
    # 转换PDF为图片
    images = convert_from_path(
        pdf_path, 
        dpi=dpi,
        first_page=page_number,
        last_page=page_number
    )
    
    if not images:
        raise ValueError(f"无法转换页码 {page_number}，可能超出PDF页数范围")
    
    # 获取文件名（不含路径和扩展名）
    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # 保存图片
    image_path = os.path.join(output_dir, f"{base_filename}_page_{page_number}.{fmt}")
    images[0].save(image_path, format=fmt.upper())
    
    result = {"image_path": image_path}
    
    # 如果需要，保存单页PDF
    if save_pdf:
        pdf_path_out = os.path.join(output_dir, f"{base_filename}_page_{page_number}.pdf")
        
        # 使用PyPDF2提取单页并保存
        pdf_reader = PdfReader(pdf_path)
        pdf_writer = PdfWriter()
        
        # PyPDF2的页码从0开始，需要减1
        if page_number <= len(pdf_reader.pages):
            pdf_writer.add_page(pdf_reader.pages[page_number-1])
            
            # 保存提取的页面到新PDF
            with open(pdf_path_out, "wb") as output_pdf:
                pdf_writer.write(output_pdf)
            
            result["pdf_path"] = pdf_path_out
        else:
            raise ValueError(f"页码 {page_number} 超出PDF页数范围")
    
    return result


if __name__ == "__main__":
    # 使用示例
    pdf_file = "example.pdf"
    page_to_convert = 1  # 转换第一页
    
    try:
        result = pdf_to_image(pdf_file, page_to_convert, save_pdf=True)
        print(f"图片已保存至: {result['image_path']}")
        if 'pdf_path' in result:
            print(f"PDF单页已保存至: {result['pdf_path']}")
    except Exception as e:
        print(f"转换过程中出错: {e}")
