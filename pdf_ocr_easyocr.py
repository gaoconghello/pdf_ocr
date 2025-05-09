import os
import argparse
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import easyocr
from pdf_to_img import pdf_to_image


def ocr_pdf_page(pdf_path, page_number, output_dir='output', lang='ch', save_result=True, dpi=300):
    """
    对PDF指定页面进行OCR识别，使用EasyOCR引擎
    
    Args:
        pdf_path: PDF文件路径
        page_number: 需要识别的页码（从1开始）
        output_dir: 输出目录
        lang: OCR识别的语言，支持多种语言如'ch_sim'(简体中文),'en'(英文)等
        save_result: 是否保存识别结果图片
        dpi: 转换PDF时的DPI值
    
    Returns:
        识别结果和结果图片路径(如果save_result=True)
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 将PDF转换为图片
    image_path = pdf_to_image(pdf_path, page_number, output_dir, dpi)
    
    # 初始化OCR模型
    # 语言映射，将简单的语言代码映射到EasyOCR支持的语言代码
    lang_map = {
        'ch': 'ch_sim',  # 简体中文
        'en': 'en',      # 英文
        'japan': 'ja',   # 日语
        'korean': 'ko',  # 韩语
        'french': 'fr',  # 法语
        'german': 'de',  # 德语
    }
    
    # 获取实际使用的语言
    ocr_lang = lang_map.get(lang, lang)
    
    # 如果是中文识别，加上英文提高识别效果
    if ocr_lang == 'ch_sim':
        reader = easyocr.Reader(['ch_sim', 'en'])
    else:
        reader = easyocr.Reader([ocr_lang])
    
    # 执行OCR识别
    result = reader.readtext(image_path)
    
    # 保存处理结果
    result_info = []
    for line in result:
        box = line[0]  # 文本框坐标
        text = line[1]  # 识别的文本
        confidence = line[2]  # 置信度
        result_info.append({
            'box': box,
            'text': text,
            'confidence': confidence
        })
    
    # 如果需要，保存可视化结果
    result_image_path = None
    if save_result:
        # 获取基础文件名
        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        result_image_path = os.path.join(output_dir, f"{base_filename}_page_{page_number}_result.png")
        
        # 绘制OCR结果
        image = Image.open(image_path).convert('RGB')
        draw = ImageDraw.Draw(image)
        
        # 尝试加载字体
        font_size = 20
        try:
            font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'simfang.ttf')
            if not os.path.exists(os.path.dirname(font_path)):
                os.makedirs(os.path.dirname(font_path))
            
            # 尝试使用系统字体
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            elif os.name == 'nt':  # Windows
                font = ImageFont.truetype("arial.ttf", font_size)
            else:  # Linux/Mac
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except Exception:
            # 如果无法加载字体，使用默认字体
            font = ImageFont.load_default()
        
        # 绘制文本框和文字
        for item in result_info:
            box = item['box']
            text = item['text']
            confidence = item['confidence']
            
            # 绘制矩形框
            draw.polygon([tuple(p) for p in box], outline=(0, 255, 0), width=2)
            
            # 绘制文本
            text_position = (box[0][0], box[0][1] - font_size)
            draw.text(text_position, f"{text} ({confidence:.2f})", fill=(255, 0, 0), font=font)
        
        # 保存结果图片
        image.save(result_image_path)
    
    return result_info, result_image_path


def main():
    parser = argparse.ArgumentParser(description='PDF OCR识别工具 (EasyOCR)')
    parser.add_argument('pdf_path', help='PDF文件路径')
    parser.add_argument('page_number', type=int, help='需要识别的页码（从1开始）')
    parser.add_argument('--output_dir', default='output', help='输出目录')
    parser.add_argument('--lang', default='ch', help='OCR识别语言，支持ch, en, japan, korean, french, german等')
    parser.add_argument('--no_save_result', action='store_true', help='不保存识别结果图片')
    parser.add_argument('--dpi', type=int, default=300, help='PDF转图片的DPI值')
    
    args = parser.parse_args()
    
    try:
        result_info, result_image_path = ocr_pdf_page(
            args.pdf_path,
            args.page_number,
            args.output_dir,
            args.lang,
            not args.no_save_result,
            args.dpi
        )
        
        print(f"\n--- OCR识别结果 ---")
        for item in result_info:
            print(f"文本: {item['text']}, 置信度: {item['confidence']:.4f}")
        
        if result_image_path:
            print(f"\n识别结果图片已保存至: {result_image_path}")
            
    except Exception as e:
        print(f"OCR识别过程中出错: {e}")


if __name__ == "__main__":
    main()
