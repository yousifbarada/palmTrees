# export.py
import os
from datetime import datetime

def save_report_as_pdf_arabic(report, tree_id):
    html_filename = f"palm_tree_{tree_id}_report.html"
    
    # Your original extensive HTML template goes here
    html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>تقرير شجرة النخيل رقم {tree_id}</title>
    </head>
<body>
    <div class="container">
        <div class="header-section">
            <div class="header">🌴 تقرير شجرة النخيل</div>
            <div class="header-subtitle">رقم الشجرة: #{tree_id}</div>
        </div>
        <div class="meta-info">
            <div class="meta-item">
                <div class="meta-label">📅 التاريخ:</div>
                <div class="meta-value">{datetime.now().strftime('%Y-%m-%d')}</div>
            </div>
        </div>
        <div class="content">
"""
    # Logic to parse the markdown string into HTML lists
    lines = report.split('\n')
    current_section = None
    list_stack = []
    
    for line in lines:
        original_line = line
        line = line.strip()
        if not line: continue
        
        indent_level = len(original_line) - len(original_line.lstrip())
        indent_level = indent_level // 2
        
        if any(marker in line for marker in ['**', '###', '##']):
            while list_stack:
                html_content += "</ul>"
                list_stack.pop()
            if current_section: html_content += "</div>"
            
            clean_line = line.replace('**', '').replace('##', '').replace('###', '').strip()
            html_content += f'<div class="section"><div class="section-title">{clean_line}</div>'
            current_section = True
        else:
            if current_section:
                if line.startswith('*') or line.startswith('•') or line.startswith('-'):
                    clean_text = line.lstrip('*•-').strip()
                    target_level = max(0, indent_level)
                    while len(list_stack) > target_level:
                        html_content += "</ul>"
                        list_stack.pop()
                    while len(list_stack) <= target_level:
                        html_content += "<ul>"
                        list_stack.append(True)
                    html_content += f'<li>{clean_text}</li>'
                else:
                    while list_stack:
                        html_content += "</ul>"
                        list_stack.pop()
                    html_content += f'<p>{line}</p>'
            else:
                html_content += f'<p>{line}</p>'
                
    while list_stack:
        html_content += "</ul>"
        list_stack.pop()
    if current_section:
        html_content += "</div>"
        
    html_content += "</div></div></body></html>"

    try:
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ تم حفظ التقرير كـ HTML: {html_filename}")
        
        txt_filename = f"palm_tree_{tree_id}_report.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"تقرير شجرة النخيل رقم {tree_id}\n\n{report}")
        print(f"✅ تم حفظ النسخة النصية: {txt_filename}")
        
        try:
            from xhtml2pdf import pisa
            pdf_filename = f"palm_tree_{tree_id}_report.pdf"
            with open(pdf_filename, 'wb') as pdf_file:
                pisa.CreatePDF(html_content, pdf_file)
            print(f"✅ تم حفظ التقرير كـ PDF: {pdf_filename}")
        except ImportError:
            print("⚠️ مكتبة xhtml2pdf غير مثبتة.")
            
        return html_filename
    except Exception as e:
        print(f"❌ خطأ في الحفظ: {e}")
        return None