import os
import argparse
from PIL import Image
from paddleocr import PaddleOCR, draw_ocr
from pdf_to_img import pdf_to_image


def ocr_pdf_page(pdf_path, page_number, output_dir='output', lang='ch', save_result=True, dpi=300):
    """
    对PDF指定页面进行OCR识别
    
    Args:
        pdf_path: PDF文件路径
        page_number: 需要识别的页码（从1开始）
        output_dir: 输出目录
        lang: OCR识别的语言，支持'ch'(中文),'en'(英文),'french','german','korean','japan'等
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
    ocr = PaddleOCR(use_angle_cls=True, lang=lang)
    
    # 执行OCR识别
    result = ocr.ocr(image_path, cls=True)
    
    # 保存处理结果
    result_info = []
    for line in result[0]:
        box = line[0]  # 文本框坐标
        text = line[1][0]  # 识别的文本
        confidence = line[1][1]  # 置信度
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
        boxes = [line[0] for line in result[0]]
        txts = [line[1][0] for line in result[0]]
        scores = [line[1][1] for line in result[0]]
        
        # 绘制结果并保存
        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'simfang.ttf')
        if not os.path.exists(os.path.dirname(font_path)):
            os.makedirs(os.path.dirname(font_path))
            # 如果没有字体文件，可以使用系统默认字体
            # Windows系统可能路径为 C:/Windows/Fonts/simfang.ttf
            # 这里为了简便，创建一个字体目录但不强制要求字体存在
            
        # 尝试使用指定字体，如果不存在，PaddleOCR会使用默认字体
        im_show = draw_ocr(image, boxes, txts, scores, font_path=font_path)
        im_show = Image.fromarray(im_show)
        im_show.save(result_image_path)
    
    return result_info, result_image_path


def main():
    parser = argparse.ArgumentParser(description='PDF OCR识别工具')
    parser.add_argument('pdf_path', help='PDF文件路径')
    parser.add_argument('page_number', type=int, help='需要识别的页码（从1开始）')
    parser.add_argument('--output_dir', default='output', help='输出目录')
    parser.add_argument('--lang', default='ch', help='OCR识别语言，支持ch, en, french, german, korean, japan等')
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
