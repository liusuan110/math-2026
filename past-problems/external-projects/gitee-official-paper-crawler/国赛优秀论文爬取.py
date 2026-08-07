#!/usr/bin/python 3.8.9
# -*- coding: utf-8 -*- 
#
# @Time    : 2024-09-03 16:12
# @Author  : 阿发
# @Email   : fafa27182818@gmail.com
# @GitHub  : https://github.com/lovely-fafa
# @File    : 国赛优秀论文爬取.py
# @Software: PyCharm

import re
import os
from pathlib import Path
from traceback import print_exc

import img2pdf
from lxml import etree, html
from tqdm import tqdm
import requests

print('欢迎使用软件，版本V1.1')
print('软件更新与项目地址为：https://gitee.com/CUITsxjm/China-University-Students-Online-Website-National-Competition-Outstanding-Papers-Crawling')
print('\n' + '=' * 50)

try:
    # 'https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2023qgdxssxjmjslwzs_2023ctlw/231104/1865124.shtml'
    url = input('请输入 中国大学生在线网站 国赛优秀论文 网址（例如'
                'https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2023qgdxssxjmjslwzs_2023ctlw/231104/1865124.shtml）程序不会校验网址合法性：')
    resp = requests.get(url)
    resp_text = resp.text
    title = re.search(r'<div class="detail-tit">(.*?)<', resp_text, re.S)
    code = re.search(r'(20\d\d)', resp_text).group(1) + '-' + re.search(r'([A-E]\d+)', resp_text).group(1)

    OUTPUT = Path('miao') / code
    os.makedirs(OUTPUT, exist_ok=True)

    h = etree.HTML(resp_text)
    images = html.tostring(h.xpath('//div[@class="imagesgroup box"]/div')[0], encoding='unicode')
    for index, pic_url in enumerate(tqdm(re.findall(r'<img src="(.*?)"', images))):
        if not pic_url.startswith('http'):
            pic_url = f'https://dxs.moe.gov.cn{pic_url}'
        if 'jpg' in pic_url.lower():
            suffix = '.jpg'
        elif 'png' in pic_url.lower():
            suffix = '.png'
        else:
            suffix = '.png'
        with open(OUTPUT / f'{str(index).zfill(3)}{suffix}', mode='wb') as f:
            f.write(requests.get(pic_url).content)

    images = list(OUTPUT.glob('*'))
    with open(Path('miao') / (code + '.pdf'), mode='wb') as f:
        write_content = img2pdf.convert(images)
        f.write(write_content)
except:
    print('哦豁报错了呜呜')
    print_exc()

input('输入喵退出程序...')
