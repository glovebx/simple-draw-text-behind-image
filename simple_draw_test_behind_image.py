import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import time
import torch
from transformers import AutoModelForImageSegmentation
from utilities import preprocess_image, postprocess_image

def remove_background_and_shrink(input_path, output_path, dilation_size=12, shrink_pixels=5):
    # Load the model
    net = AutoModelForImageSegmentation.from_pretrained("briaai/RMBG-1.4", trust_remote_code=True)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    net.to(device)

    filename = input_path.split("/")[-1]
    model_input_size = [1024, 1024]
    orig_im = np.array(Image.open(input_path))
    orig_im_size = orig_im.shape[0:2]
    image = preprocess_image(orig_im, model_input_size)
    result = net(image)
    result_image = postprocess_image(result[0][0], orig_im_size)

    pil_im = Image.fromarray(result_image)
    no_bg_image = Image.new("RGBA", pil_im.size, (0, 0, 0, 0))
    orig_image = Image.open(input_path)
    no_bg_image.paste(orig_image, mask=pil_im)
    no_bg_image.save(output_path)

def add_centered_text(image_path, text, font_path, font_size, output_path):
    # 打开背景图片
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        
        # 加载字体
        font = ImageFont.truetype(font_path, font_size)
        
        # 获取图片尺寸
        img_width, img_height = img.size
        
        # 计算可用文本区域（左右margin为32像素）
        text_width = img_width - 64
        
        # 根据文本长度调整字间距
        if len(text) < 10:
            # 如果文本很短，增加字间距
            spacing = int(font_size * 0.2)  # 可以根据需要调整这个值
        else:
            spacing = 12
        
        # 自定义中文文本换行函数
        def wrap_chinese(text, width):
            lines = []
            line = ""
            for char in text:
                char_width = font.getbbox(char)[2] - font.getbbox(char)[0]
                if font.getbbox(line + char)[2] - font.getbbox(line + char)[0] <= width:
                    line += char
                else:
                    lines.append(line)
                    line = char
            if line:
                lines.append(line)
            return lines
        
        # 使用自定义函数进行换行
        lines = wrap_chinese(text, text_width)
        
        # 计算文本高度
        line_height = font.getbbox('中')[3] + spacing
        text_height = len(lines) * line_height
        
        # 计算文本起始位置（居中）
        x = (img_width - text_width) // 2
        # y = (img_height - text_height) // 2
        y = 100

        # 绘制文本
        for line in lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_x = (img_width - line_width) // 2
            draw.text((line_x, y), line, font=font, fill=(255, 255, 255))  # 白色文字
            y += line_height
        
        # 保存结果
        img.save(output_path)

def overlay_images(background_path, overlay_path, output_path, position=(0, 0)):
    # 打开背景图片
    background = Image.open(background_path)
    
    # 打开要叠加的透明PNG图片
    overlay = Image.open(overlay_path)
    
    # 确保overlay图片有透明通道
    if overlay.mode != 'RGBA':
        overlay = overlay.convert('RGBA')
    
    # 创建一个与背景图片大小相同的空白图片
    new_image = Image.new('RGBA', background.size, (0, 0, 0, 0))
    
    # 将背景图片粘贴到新图片上
    new_image.paste(background, (0, 0))
    
    # 将透明PNG叠加到指定位置
    new_image.paste(overlay, position, overlay)
    
    # 保存结果
    new_image.save(output_path)

# 使用示例
text = "肖像画大师约翰·辛格·萨金特作品的魅力"
font_path = "ZiHunBianTaoTi-2.ttf"
font_size = 128

background_path = "background.jpg"
overlay_path = "overlay.png"
texted_background_path = "texted_background.png"
final_image_path = "final_image.png"

remove_background_and_shrink(background_path, overlay_path)
add_centered_text(background_path, text, font_path, font_size, texted_background_path)
overlay_images(texted_background_path, overlay_path, final_image_path)
