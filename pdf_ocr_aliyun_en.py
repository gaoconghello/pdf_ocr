# -*- coding: utf-8 -*-
import os
import sys
import io
import json
import enum
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

from pdf2image import convert_from_path
from PIL import Image

from alibabacloud_ocr_api20210707.client import Client as ocr_api20210707Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.models import Config as CredentialConfig  
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ocr_api20210707 import models as ocr_api_20210707_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

# --- 请根据您的实际情况修改以下配置 ---
PDF_FILE_PATH = "1.pdf"  # 要识别的 PDF 文件路径
POPPLER_PATH = r"E:\Tools\poppler-24.08.0\Library\bin"  # Poppler 的 bin 目录路径
OUTPUT_DIR = Path("output")
SAVE_IMAGES = True  # 是否保存转换后的图片
LANGUAGE = "ENGLISH"  # 设置识别语言，可选值: "ENGLISH", "JAPANESE", "RUSSIAN", "KOREAN", "THAI", "LATIN", "MULTILANGUAGE"
# --- 配置结束 ---

# 加载 .env 文件中的环境变量
load_dotenv()

OUTPUT_DIR.mkdir(exist_ok=True)

# 创建图片保存目录
IMAGES_DIR = OUTPUT_DIR / "images"
if SAVE_IMAGES:
    IMAGES_DIR.mkdir(exist_ok=True)


class LanguageType(enum.Enum):
    """支持的语言类型枚举"""
    ENGLISH = "ENGLISH"
    JAPANESE = "JAPANESE"
    RUSSIAN = "RUSSIAN"
    KOREAN = "KOREAN"
    THAI = "THAI"
    LATIN = "LATIN"
    MULTILANGUAGE = "MULTILANGUAGE"


class AliyunOcrProcessor:
    def __init__(self, language: str = "ENGLISH"):
        self.client = self._create_client()
        try:
            self.language = LanguageType[language.upper()]
        except KeyError:
            print(f"警告：不支持的语言类型 '{language}'，默认使用英语识别。")
            print(f"支持的语言类型: {', '.join([lang.name for lang in LanguageType])}")
            self.language = LanguageType.ENGLISH

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

    def recognize_text_from_image_bytes(self, image_bytes: bytes) -> str:
        """根据选择的语言调用对应的小语种识别API"""
        runtime = util_models.RuntimeOptions()
        
        try:
            if self.language == LanguageType.ENGLISH:
                request = ocr_api_20210707_models.RecognizeEnglishRequest(body=image_bytes)
                response = self.client.recognize_english_with_options(request, runtime)
            elif self.language == LanguageType.JAPANESE:
                request = ocr_api_20210707_models.RecognizeJanpaneseRequest(body=image_bytes)
                response = self.client.recognize_janpanese_with_options(request, runtime)
            elif self.language == LanguageType.RUSSIAN:
                request = ocr_api_20210707_models.RecognizeRussianRequest(body=image_bytes)
                response = self.client.recognize_russian_with_options(request, runtime)
            elif self.language == LanguageType.KOREAN:
                request = ocr_api_20210707_models.RecognizeKoreanRequest(body=image_bytes)
                response = self.client.recognize_korean_with_options(request, runtime)
            elif self.language == LanguageType.THAI:
                request = ocr_api_20210707_models.RecognizeThaiRequest(body=image_bytes)
                response = self.client.recognize_thai_with_options(request, runtime)
            elif self.language == LanguageType.LATIN:
                request = ocr_api_20210707_models.RecognizeLatinRequest(body=image_bytes)
                response = self.client.recognize_latin_with_options(request, runtime)
            elif self.language == LanguageType.MULTILANGUAGE:
                request = ocr_api_20210707_models.RecognizeMultiLanguageRequest(body=image_bytes)
                response = self.client.recognize_multi_language_with_options(request, runtime)
            else:
                print(f"不支持的语言类型: {self.language}")
                return ""
            
            # 检查响应状态
            if not response or not response.body:
                print("API响应为空")
                return ""
                
            # 根据文档，Data字段包含JSON字符串，需要先解析
            if response.body.data:
                try:
                    # 解析JSON字符串为Python字典
                    data_dict = json.loads(response.body.data)
                    
                    # 小语种识别返回格式可能与手写体识别不同，根据API返回格式进行提取
                    
                    # 检查常见的文本内容字段
                    if "content" in data_dict:
                        return data_dict["content"]
                    
                    # 检查小语种识别可能用的字段
                    if "prism_version" in data_dict and "text" in data_dict:
                        return data_dict["text"]
                        
                    # 检查是否有行信息
                    if "prism_wordsInfo" in data_dict and isinstance(data_dict["prism_wordsInfo"], list):
                        words = []
                        for word_info in data_dict["prism_wordsInfo"]:
                            if "word" in word_info:
                                words.append(word_info["word"])
                        return " ".join(words)
                    
                    # 如果有行信息数组
                    if "lines" in data_dict and isinstance(data_dict["lines"], list):
                        lines = []
                        for line in data_dict["lines"]:
                            if "text" in line:
                                lines.append(line["text"])
                        return "\n".join(lines)
                    
                    # 如果都没有，返回原始数据以便调试
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
        """处理PDF文件，对每一页进行小语种OCR识别并保存结果"""
        if not Path(pdf_path).exists():
            print(f"错误：PDF文件未找到: {pdf_path}")
            return

        try:
            pages = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
        except Exception as e:
            print(f"PDF转换为图片失败: {e}")
            print(f"请确保已安装pdf2image和Poppler，并且Poppler路径配置正确: {poppler_path}")
            return

        print(f"正在使用【{self.language.name}】语言模式进行识别...")
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

            recognized_text = self.recognize_text_from_image_bytes(image_bytes)
            if recognized_text:
                page_output_path = OUTPUT_DIR / f"page_{i:03d}.txt"
                page_output_path.write_text(recognized_text, encoding='utf-8')
                print(f"  第 {i} 页识别结果已保存到: {page_output_path}")
                all_recognized_text.append(recognized_text)
            else:
                print(f"  第 {i} 页未能识别出文本或API调用失败。")

        if all_recognized_text:
            lang_suffix = self.language.name.lower()
            full_text_output_path = OUTPUT_DIR / f"{Path(pdf_path).stem}_ocr_{lang_suffix}.txt"
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

    # 创建OCR处理器并指定语言
    processor = AliyunOcrProcessor(LANGUAGE)
    processor.process_pdf(PDF_FILE_PATH, POPPLER_PATH)


if __name__ == '__main__':
    main()
