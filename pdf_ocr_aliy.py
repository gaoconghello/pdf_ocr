# -*- coding: utf-8 -*-
import os
import sys
import io
import json
from typing import List
from pathlib import Path
from dotenv import load_dotenv # 新增导入

from pdf2image import convert_from_path
from PIL import Image

from alibabacloud_ocr_api20210707.client import Client as ocr_api20210707Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.models import Config as CredentialConfig  
from alibabacloud_tea_openapi import models as open_api_models
# from alibabacloud_darabonba_stream.client import Client as StreamClient # Not needed if passing bytes directly
from alibabacloud_ocr_api20210707 import models as ocr_api_20210707_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

# --- 请根据您的实际情况修改以下配置 ---
PDF_FILE_PATH = "1.pdf"  # 要识别的 PDF 文件路径
POPPLER_PATH = r"E:\Tools\poppler-24.08.0\Library\bin"  # Poppler 的 bin 目录路径
OUTPUT_DIR = Path("output")
SAVE_IMAGES = True  # 是否保存转换后的图片
# --- 配置结束 ---

# 加载 .env 文件中的环境变量
load_dotenv()

OUTPUT_DIR.mkdir(exist_ok=True)

# 创建图片保存目录
IMAGES_DIR = OUTPUT_DIR / "images"
if SAVE_IMAGES:
    IMAGES_DIR.mkdir(exist_ok=True)


class AliyunOcrProcessor:
    def __init__(self):
        self.client = self._create_client()

    @staticmethod
    def _create_client() -> ocr_api20210707Client:
        """
        使用凭据初始化账号Client
        @return: Client
        @throws Exception
        """
        try:
            # 从环境变量中获取AccessKey信息
            access_key_id = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID')
            access_key_secret = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET')

            if not access_key_id or not access_key_secret:
                print("错误：环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID 或 ALIBABA_CLOUD_ACCESS_KEY_SECRET 未设置。")
                sys.exit(1)

            cred_config = CredentialConfig(
                type='access_key',
                access_key_id=access_key_id,
                access_key_secret=access_key_secret
            )
            credential = CredentialClient(cred_config)
        except Exception as e:
            print(f"创建阿里云凭证客户端失败: {e}")
            sys.exit(1)

        config = open_api_models.Config(
            credential=credential
        )
        # Endpoint 请参考 https://api.aliyun.com/product/ocr-api
        config.endpoint = 'ocr-api.cn-hangzhou.aliyuncs.com'
        return ocr_api20210707Client(config)

    def recognize_handwriting_from_image_bytes(self, image_bytes: bytes) -> str:
        """调用阿里云手写体识别API"""
        recognize_handwriting_request = ocr_api_20210707_models.RecognizeHandwritingRequest(
            body=image_bytes,  # 直接传递图像的二进制数据
            output_char_info=False, # 根据需求调整，True会输出单字信息
            need_rotate=True,      # 允许自动旋转
            output_table=False,    # 如果不需要表格识别，设为False
            need_sort_page=True,   # 按顺序输出文字块
            paragraph=True         # 需要分段
        )
        runtime = util_models.RuntimeOptions()
        try:
            response = self.client.recognize_handwriting_with_options(recognize_handwriting_request, runtime)
            
            # 检查响应状态
            if not response or not response.body:
                print("API响应为空")
                return ""
                
            # 根据文档，Data字段包含JSON字符串，需要先解析
            if response.body.data:
                try:
                    # 解析JSON字符串为Python字典
                    data_dict = json.loads(response.body.data)
                    
                    # 从解析后的字典中提取内容
                    # 根据阿里云文档，手写体识别返回的内容在content字段中
                    if "content" in data_dict:
                        return data_dict["content"]
                    
                    # 如果使用了段落识别，可能在prism_paragraphsInfo中
                    if "prism_paragraphsInfo" in data_dict and isinstance(data_dict["prism_paragraphsInfo"], list):
                        paragraphs = []
                        for paragraph in data_dict["prism_paragraphsInfo"]:
                            if "word" in paragraph:
                                paragraphs.append(paragraph["word"])
                        return "\n".join(paragraphs)
                    
                    # 如果以上都没有，尝试从wordsInfo中提取
                    if "prism_wordsInfo" in data_dict and isinstance(data_dict["prism_wordsInfo"], list):
                        words = []
                        for word_info in data_dict["prism_wordsInfo"]:
                            if "word" in word_info:
                                words.append(word_info["word"])
                        return " ".join(words)
                    
                    print("在API返回中未找到文本内容。返回数据:")
                    print(data_dict)
                    return ""
                    
                except json.JSONDecodeError as e:
                    print(f"解析API返回的JSON数据失败: {e}")
                    print(f"原始数据: {response.body.data}")
                    return ""
            else:
                print("API响应中没有Data字段")
                if response.body.message:
                    print(f"API错误信息: {response.body.message}")
                return ""
                
        except Exception as error:
            error_msg = error.message if hasattr(error, 'message') else str(error)
            print(f"调用阿里云OCR API失败: {error_msg}")
            if hasattr(error, 'data') and error.data and hasattr(error.data, "get") and error.data.get("Recommend"):
                print(f"诊断地址: {error.data.get('Recommend')}")
            return ""

    def process_pdf(self, pdf_path: str, poppler_path: str):
        """处理PDF文件，对每一页进行OCR识别并保存结果"""
        if not Path(pdf_path).exists():
            print(f"错误：PDF文件未找到: {pdf_path}")
            return

        try:
            pages = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
        except Exception as e:
            print(f"PDF转换为图片失败: {e}")
            print(f"请确保已安装pdf2image和Poppler，并且Poppler路径配置正确: {poppler_path}")
            return

        all_recognized_text = []
        for i, page_image in enumerate(pages, 1):
            print(f"正在处理第 {i}/{len(pages)} 页...")
            
            # 保存图片
            if SAVE_IMAGES:
                image_filename = f"page_{i:03d}.png"
                image_path = IMAGES_DIR / image_filename
                page_image.save(image_path, format='PNG')
                print(f"  已保存图片到: {image_path}")
            
            # 将Pillow Image对象转换为bytes
            img_byte_arr = io.BytesIO()
            page_image.save(img_byte_arr, format='PNG') # 阿里云支持PNG, JPG, JPEG等
            image_bytes = img_byte_arr.getvalue()

            recognized_text = self.recognize_handwriting_from_image_bytes(image_bytes)
            if recognized_text:
                page_output_path = OUTPUT_DIR / f"page_{i:03d}.txt"
                page_output_path.write_text(recognized_text, encoding='utf-8')
                print(f"  第 {i} 页识别结果已保存到: {page_output_path}")
                all_recognized_text.append(recognized_text)
            else:
                print(f"  第 {i} 页未能识别出文本或API调用失败。")

        if all_recognized_text:
            full_text_output_path = OUTPUT_DIR / f"{Path(pdf_path).stem}_ocr_aliy.txt"
            full_text_output_path.write_text("\n\n---\n\n".join(all_recognized_text), encoding='utf-8')
            print(f"🎉 所有页面识别完成！结果已汇总到: {full_text_output_path}")
        else:
            print("未能在PDF中识别到任何文本。")


def main():
    # 检查PDF文件是否存在
    if not Path(PDF_FILE_PATH).is_file():
        print(f"错误: PDF文件 '{PDF_FILE_PATH}' 不存在或不是一个文件。")
        print("请在脚本顶部正确配置 PDF_FILE_PATH 常量。")
        return

    # 检查Poppler路径是否存在
    if POPPLER_PATH and not Path(POPPLER_PATH).is_dir():
        print(f"警告: Poppler路径 '{POPPLER_PATH}' 不存在或不是一个目录。")
        print("如果PDF转换失败，请检查此路径配置。")

    processor = AliyunOcrProcessor()
    processor.process_pdf(PDF_FILE_PATH, POPPLER_PATH)


if __name__ == '__main__':
    main()