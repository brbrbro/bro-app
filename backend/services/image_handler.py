import os
from PIL import Image, ImageEnhance
import pytesseract  # OCR

class ImageHandler:
    """处理题目相关图片"""
    
    def __init__(self):
        self.image_dir = '/var/www/bro/static/images'
    
    def enhance_image(self, image_path: str) -> str:
        """增强图片质量，提高 OCR 准确率"""
        img = Image.open(image_path)
        
        if img.mode != 'L':
            img = img.convert('L')
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        filename = f"enhanced_{os.path.basename(image_path)}"
        enhanced_path = os.path.join(self.image_dir, filename)
        img.save(enhanced_path)
        
        return enhanced_path
    
    def ocr_image(self, image_path: str, lang: str = 'chi_sim+eng') -> str:
        """OCR 识别图片文字"""
        try:
            enhanced_path = self.enhance_image(image_path)
            text = pytesseract.image_to_string(enhanced_path, lang=lang)
            return text.strip()
        except Exception as e:
            print(f"OCR 错误: {e}")
            return ""
    
    def detect_formulas(self, image_path: str) -> list:
        """检测图片中的公式区域（简化版）"""
        return []
    
    def save_base64_image(self, base64_data: str, filename: str) -> str:
        """保存 base64 编码的图片"""
        import base64
        image_data = base64.b64decode(base64_data)
        image_path = os.path.join(self.image_dir, filename)
        with open(image_path, 'wb') as f:
            f.write(image_data)
        return image_path
