# 不可行
# from weasyprint import HTML
#
# url = 'https://freedium.cfd/https://medium.com/itnext/daily-bit-e-of-c-optimizing-code-to-run-87x-faster-7ef0b5bc64a1?source=explore---------0-99--------------------bb152417_3af1_40a7_8833_4501f789e289-------15'
# output_path = 'article.pdf'
#
# HTML(url).write_pdf('article')
import uuid

import pdfkit

def save_as_pdf(url, output_path):
    # 替换为你的 wkhtmltopdf 可执行文件的实际路径
    path_to_wkhtmltopdf = r'D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    pdfkit.from_url(url, output_path, configuration=config)

# 示例使用
url = 'https://freedium.cfd/https://medium.com/itnext/daily-bit-e-of-c-optimizing-code-to-run-87x-faster-7ef0b5bc64a1?source=explore---------0-99--------------------bb152417_3af1_40a7_8833_4501f789e289-------15'
id=uuid.uuid4()
output_path = r'D:\articles\article'+str(id)
save_as_pdf(url, output_path)


