# export.py
import os
from datetime import datetime


# ─────────────────────────────────────────────
#  Helper: parse markdown lines → HTML blocks
# ─────────────────────────────────────────────
def _markdown_to_html_blocks(report: str) -> str:
    """Convert a markdown-style report string into styled HTML sections."""
    html = ""
    lines = report.split('\n')
    current_section = False
    list_stack = []

    for line in lines:
        original_line = line
        line = line.strip()
        if not line:
            continue

        indent_level = (len(original_line) - len(original_line.lstrip())) // 2

        if any(marker in line for marker in ['**', '###', '##']):
            while list_stack:
                html += "</ul>"
                list_stack.pop()
            if current_section:
                html += "</div>"

            clean_line = line.replace('**', '').replace('##', '').replace('###', '').strip()
            html += f'<div class="section"><div class="section-title">{clean_line}</div>'
            current_section = True

        else:
            if current_section:
                if line.startswith(('*', '•', '-')):
                    clean_text = line.lstrip('*•-').strip()
                    target_level = max(0, indent_level)
                    while len(list_stack) > target_level:
                        html += "</ul>"
                        list_stack.pop()
                    while len(list_stack) <= target_level:
                        html += "<ul>"
                        list_stack.append(True)
                    html += f'<li>{clean_text}</li>'
                else:
                    while list_stack:
                        html += "</ul>"
                        list_stack.pop()
                    html += f'<p>{line}</p>'
            else:
                html += f'<p>{line}</p>'

    while list_stack:
        html += "</ul>"
        list_stack.pop()
    if current_section:
        html += "</div>"

    return html


# ─────────────────────────────────────────────────────────────────────────────
#  CSS for browser (HTML file) — supports Google Fonts + CSS variables
# ─────────────────────────────────────────────────────────────────────────────
_CSS_HTML = """
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&display=swap');

    :root {
        --sand:       #f5ede0;
        --sand-dark:  #e8d9c4;
        --bark:       #5c3d1e;
        --bark-light: #8b6340;
        --leaf:       #2d6a4f;
        --leaf-light: #52b788;
        --gold:       #c9932a;
        --text:       #2c1a0e;
        --text-muted: #7a5c3a;
        --white:      #fffdf9;
        --shadow:     rgba(92,61,30,.15);
        --danger:     #c0392b;
        --warning:    #e67e22;
        --ok:         #27ae60;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        font-family: 'Tajawal', sans-serif;
        background: #f5ede0;
        color: #2c1a0e;
        direction: rtl;
        min-height: 100vh;
    }

    .container {
        max-width: 920px;
        margin: 40px auto;
        background: #fffdf9;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 40px rgba(92,61,30,.15);
    }

    .header-section {
        background: linear-gradient(135deg, #2d6a4f 0%, #1b4332 60%, #5c3d1e 100%);
        padding: 48px 40px 36px;
        position: relative;
        overflow: hidden;
    }
    .header-section::before {
        content: '🌴';
        position: absolute;
        left: -20px; top: -10px;
        font-size: 160px;
        opacity: .07;
        line-height: 1;
        pointer-events: none;
    }
    .header          { font-size: 2rem; font-weight: 900; color: #fff; margin-bottom: 8px; }
    .header-subtitle { font-size: 1.1rem; font-weight: 500; color: #52b788; }

    .meta-info {
        display: flex; flex-wrap: wrap; gap: 12px;
        background: #e8d9c4;
        padding: 16px 40px;
        border-bottom: 2px solid #f5ede0;
    }
    .meta-item  { display: flex; align-items: center; gap: 8px; }
    .meta-label { font-size: .85rem; font-weight: 700; color: #7a5c3a; text-transform: uppercase; letter-spacing: .05em; }
    .meta-value { font-size: .95rem; font-weight: 500; color: #5c3d1e; }

    .content { padding: 36px 40px 48px; }

    .section {
        margin-bottom: 28px;
        border-radius: 12px;
        background: #f5ede0;
        overflow: hidden;
        border: 1px solid #e8d9c4;
    }
    .section-title {
        font-size: 1.1rem; font-weight: 700;
        color: #fffdf9;
        background: linear-gradient(90deg, #2d6a4f, #8b6340);
        padding: 12px 20px;
        display: flex; align-items: center; gap: 8px;
    }
    .section p            { font-size: .95rem; line-height: 1.8; color: #2c1a0e; padding: 14px 20px 0; }
    .section p:last-child { padding-bottom: 14px; }
    .content > p          { font-size: .95rem; line-height: 1.8; margin-bottom: 12px; color: #2c1a0e; }

    .section ul           { list-style: none; padding: 12px 20px 14px; }
    .section ul ul        { padding: 4px 20px 4px 0; margin-top: 2px; }
    .section li           { position: relative; font-size: .92rem; line-height: 1.7; color: #2c1a0e; padding-right: 22px; margin-bottom: 4px; }
    .section li::before   { content: ''; position: absolute; right: 6px; top: .65em; width: 7px; height: 7px; background: #c9932a; border-radius: 50%; }
    .section ul ul li::before { width: 5px; height: 5px; background: #52b788; right: 8px; }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 16px; margin-bottom: 32px;
    }
    .stat-card  { background: #f5ede0; border: 1px solid #e8d9c4; border-radius: 12px; padding: 20px 16px; text-align: center; }
    .stat-value { font-size: 2rem; font-weight: 900; color: #5c3d1e; }
    .stat-label { font-size: .8rem; font-weight: 600; color: #7a5c3a; margin-top: 4px; }

    .tree-card        { margin-bottom: 16px; border-radius: 12px; border: 1px solid #e8d9c4; overflow: hidden; }
    .tree-card-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; background: #e8d9c4; cursor: pointer; user-select: none; }
    .tree-card-header:hover { background: #ddd0b8; }
    .tree-card-title  { font-size: 1rem; font-weight: 700; color: #5c3d1e; }
    .tree-card-badge  { font-size: .78rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; color: #fff; }
    .badge-high    { background: #c0392b; }
    .badge-medium  { background: #e67e22; }
    .badge-low     { background: #27ae60; }
    .badge-unknown { background: #7a5c3a; }

    .tree-card-body      { display: none; padding: 0; }
    .tree-card-body.open { display: block; }

    .crop-divider { border: none; border-top: 2px dashed #e8d9c4; margin: 32px 0; }

    @media print {
        body { background: #fff; }
        .container { box-shadow: none; margin: 0; border-radius: 0; }
        .header-section { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        .tree-card-body { display: block !important; }
    }
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CSS for xhtml2pdf (PDF rendering)
#  Rules: no CSS variables, no @import, no Google Fonts,
#         no box-shadow, no linear-gradient on text, no ::before pseudo,
#         no display:flex/grid, no border-radius on some elements.
#         Use Arabic system font stack; keep layout table-based or block-only.
# ─────────────────────────────────────────────────────────────────────────────
_CSS_PDF = """
    body {
        font-family: Arial, 'Arial Unicode MS', sans-serif;
        background: #f5ede0;
        color: #2c1a0e;
        direction: rtl;
    }

    .container {
        width: 100%;
        background: #fffdf9;
    }

    .header-section {
        background: #2d6a4f;
        padding: 24px 30px 18px;
    }
    .header          { font-size: 20pt; font-weight: bold; color: #ffffff; margin-bottom: 6px; }
    .header-subtitle { font-size: 12pt; color: #a8d8c2; }

    .meta-info   { background: #e8d9c4; padding: 10px 30px; border-bottom: 2px solid #f5ede0; }
    .meta-item   { display: block; margin-bottom: 4px; }
    .meta-label  { font-size: 8pt; font-weight: bold; color: #7a5c3a; }
    .meta-value  { font-size: 10pt; color: #5c3d1e; }

    .content     { padding: 20px 30px 30px; }
    .content > p { font-size: 10pt; line-height: 1.7; margin-bottom: 10px; color: #2c1a0e; }

    .section         { margin-bottom: 18px; border: 1px solid #e8d9c4; background: #f5ede0; }
    .section-title   { font-size: 11pt; font-weight: bold; color: #ffffff; background: #2d6a4f; padding: 8px 14px; }
    .section p       { font-size: 10pt; line-height: 1.7; color: #2c1a0e; padding: 8px 14px 0; }
    .section p:last-child { padding-bottom: 8px; }

    .section ul      { padding: 8px 28px 10px; }
    .section ul ul   { padding: 2px 24px 4px; }
    .section li      { font-size: 10pt; line-height: 1.6; color: #2c1a0e; margin-bottom: 3px; list-style-type: disc; }
    .section ul ul li{ list-style-type: circle; }

    /* Stats table (replaces CSS grid for PDF) */
    .stats-table     { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    .stats-table td  { width: 25%; text-align: center; padding: 12px 8px; border: 1px solid #e8d9c4; background: #f5ede0; }
    .stat-value      { font-size: 18pt; font-weight: bold; color: #5c3d1e; display: block; }
    .stat-label      { font-size: 8pt; font-weight: bold; color: #7a5c3a; display: block; margin-top: 3px; }

    /* Tree card for PDF — always expanded, no accordion */
    .tree-card        { margin-bottom: 14px; border: 1px solid #e8d9c4; }
    .tree-card-header { background: #e8d9c4; padding: 10px 14px; }
    .tree-card-title  { font-size: 11pt; font-weight: bold; color: #5c3d1e; }
    .tree-card-badge  { font-size: 8pt; font-weight: bold; color: #ffffff; padding: 2px 8px; }
    .badge-high    { background: #c0392b; }
    .badge-medium  { background: #e67e22; }
    .badge-low     { background: #27ae60; }
    .badge-unknown { background: #7a5c3a; }
    .tree-card-body   { display: block; padding: 0; }

    .crop-divider { border-top: 1px dashed #e8d9c4; margin: 16px 0; }
"""

_JS = """
    document.querySelectorAll('.tree-card-header').forEach(function(h) {
        h.addEventListener('click', function() {
            this.nextElementSibling.classList.toggle('open');
        });
    });
    var first = document.querySelector('.tree-card-body');
    if (first) first.classList.add('open');
"""


# ─────────────────────────────────────────────
#  Severity badge helper
# ─────────────────────────────────────────────
def _severity_badge_class(severity_text: str) -> str:
    if not severity_text:
        return "badge-unknown"
    if "عالي" in severity_text:
        return "badge-high"
    if "متوسط" in severity_text:
        return "badge-medium"
    if "منخفض" in severity_text:
        return "badge-low"
    return "badge-unknown"


def _assess_severity_inline(pest_prob: float, type_prob: float) -> str:
    avg = (pest_prob + type_prob) / 2
    if avg > 0.85:   return "عالي جداً"
    elif avg > 0.70: return "عالي"
    elif avg > 0.50: return "متوسط"
    else:            return "منخفض"


# ─────────────────────────────────────────────
#  Internal file writer
# ─────────────────────────────────────────────
def _write_files(html_content: str, html_filename: str,
                 txt_filename: str, txt_content: str,
                 pdf_base: str,
                 pdf_content: str = None) -> str | None:
    """
    html_content  — browser-ready HTML (CSS variables + Google Fonts)
    pdf_content   — xhtml2pdf-safe HTML (flat colours, no @import); falls back
                    to html_content if not provided
    """
    try:
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ تم حفظ HTML: {html_filename}")

        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        print(f"✅ تم حفظ النسخة النصية: {txt_filename}")

        try:
            from xhtml2pdf import pisa
            source = pdf_content if pdf_content is not None else html_content
            with open(pdf_base, 'wb') as pdf_file:
                pisa.CreatePDF(source.encode('utf-8'), pdf_file)
            print(f"✅ تم حفظ PDF: {pdf_base}")
        except ImportError:
            print("⚠️ مكتبة xhtml2pdf غير مثبتة.")

        return html_filename
    except Exception as e:
        print(f"❌ خطأ في الحفظ: {e}")
        return None


# ─────────────────────────────────────────────
#  1. Single-tree report  (original behaviour)
# ─────────────────────────────────────────────
def save_report_as_pdf_arabic(report: str, tree_id) -> str | None:
    """Save a diagnostic report for a single palm tree."""
    date_str      = datetime.now().strftime('%Y-%m-%d')
    base          = f"palm_tree_{tree_id}_report"
    html_filename = f"{base}.html"

    body_html = _markdown_to_html_blocks(report)

    def _build_single_tree_html(css: str) -> str:
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>تقرير شجرة النخيل رقم {tree_id}</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        <div class="header-section">
            <div class="header">&#127796; تقرير شجرة النخيل</div>
            <div class="header-subtitle">رقم الشجرة: #{tree_id}</div>
        </div>
        <div class="meta-info">
            <div class="meta-item">
                <div class="meta-label">التاريخ:</div>
                <div class="meta-value">{date_str}</div>
            </div>
        </div>
        <div class="content">{body_html}</div>
    </div>
</body>
</html>"""

    html_content = _build_single_tree_html(_CSS_HTML)
    # inject JS for accordion into browser version only
    html_content = html_content.replace('</body>', f'<script>{_JS}</script>\n</body>')
    pdf_content  = _build_single_tree_html(_CSS_PDF)

    return _write_files(
        html_content, html_filename,
        f"{base}.txt", f"تقرير شجرة النخيل رقم {tree_id}\n\n{report}",
        f"{base}.pdf",
        pdf_content=pdf_content,
    )


# ─────────────────────────────────────────────
#  2. Unified crop report  ← NEW
# ─────────────────────────────────────────────
def save_crop_report_arabic(reports: dict,
                             crop_name: str = "النخيل",
                             detection_results: dict = None) -> str | None:
    """
    Save a single unified HTML/PDF report covering ALL palm trees in the crop.

    Parameters
    ----------
    reports : dict
        {tree_id: report_text, ...}  — output of process_disease()
    crop_name : str
        Label shown in the report header.
    detection_results : dict, optional
        {tree_id: {'pest': {'label':..,'probability':..},
                   'type': {'label':..,'probability':..}}, ...}
        Provides severity badges and subtitles per tree.

    Returns
    -------
    str | None  — path to the saved HTML file, or None on error.
    """
    date_str      = datetime.now().strftime('%Y-%m-%d')
    total_trees   = len(reports)
    base          = f"crop_{crop_name}_report_{date_str}"

    # ── Stats ──────────────────────────────────────────────
    high_count = medium_count = low_count = 0
    tree_severities = {}  # tree_id → severity string

    for tid, report_text in reports.items():
        sev = ""
        if detection_results and tid in detection_results:
            det = detection_results[tid]
            if isinstance(det, dict):
                pest_prob = det.get('pest', {}).get('probability', 0)
                type_prob = det.get('type', {}).get('probability', 0)
                sev = _assess_severity_inline(pest_prob, type_prob)
        tree_severities[tid] = sev
        if "عالي" in sev:   high_count   += 1
        elif "متوسط" in sev: medium_count += 1
        elif "منخفض" in sev: low_count    += 1

    # ── Stats HTML (browser) ───────────────────────────────
    stats_html = f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{total_trees}</div>
            <div class="stat-label">إجمالي الأشجار</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color:#c0392b">{high_count}</div>
            <div class="stat-label">خطورة عالية</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color:#e67e22">{medium_count}</div>
            <div class="stat-label">خطورة متوسطة</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color:#27ae60">{low_count}</div>
            <div class="stat-label">خطورة منخفضة</div>
        </div>
    </div>"""

    # ── Stats HTML (PDF — use <table> instead of CSS grid) ──
    stats_html_pdf = f"""
    <table class="stats-table">
        <tr>
            <td><span class="stat-value">{total_trees}</span><span class="stat-label">إجمالي الأشجار</span></td>
            <td><span class="stat-value" style="color:#c0392b">{high_count}</span><span class="stat-label">خطورة عالية</span></td>
            <td><span class="stat-value" style="color:#e67e22">{medium_count}</span><span class="stat-label">خطورة متوسطة</span></td>
            <td><span class="stat-value" style="color:#27ae60">{low_count}</span><span class="stat-label">خطورة منخفضة</span></td>
        </tr>
    </table>"""

    # ── Per-tree accordion cards ────────────────────────────
    tree_cards_html = ""
    for tree_id, report_text in reports.items():
        sev         = tree_severities[tree_id]
        badge_class = _severity_badge_class(sev)
        body_html   = _markdown_to_html_blocks(report_text)

        subtitle = ""
        if detection_results and tree_id in detection_results:
            det = detection_results[tree_id]
            if isinstance(det, dict):
                pl = det.get('pest', {}).get('label', '')
                tl = det.get('type', {}).get('label', '')
                pp = det.get('pest', {}).get('probability', 0)
                subtitle = f"{pl} · {tl} · {pp*100:.0f}%"

        badge_html    = f'<span class="tree-card-badge {badge_class}">{sev}</span>' if sev else ""
        subtitle_html = (f'<span style="font-weight:400;font-size:.85rem;'
                         f'color:#7a5c3a;margin-right:8px">{subtitle}</span>'
                         if subtitle else "")

        tree_cards_html += f"""
        <div class="tree-card">
            <div class="tree-card-header">
                <span class="tree-card-title">🌴 شجرة رقم {tree_id} {subtitle_html}</span>
                {badge_html}
            </div>
            <div class="tree-card-body">{body_html}</div>
        </div>"""

    # ── Builder helper ──────────────────────────────────────
    def _build_crop_html(css: str, s_html: str, cards_html: str,
                         include_js: bool = False) -> str:
        js_block = f'<script>{_JS}</script>' if include_js else ''
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>تقرير محصول {crop_name} - {date_str}</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        <div class="header-section">
            <div class="header">&#127796; تقرير محصول {crop_name}</div>
            <div class="header-subtitle">تقرير موحد شامل لجميع الأشجار</div>
        </div>
        <div class="meta-info">
            <div class="meta-item">
                <div class="meta-label">التاريخ:</div>
                <div class="meta-value">{date_str}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">عدد الأشجار:</div>
                <div class="meta-value">{total_trees} شجرة</div>
            </div>
        </div>
        <div class="content">
            {s_html}
            <hr class="crop-divider">
            {cards_html}
        </div>
    </div>
    {js_block}
</body>
</html>"""

    html_content = _build_crop_html(_CSS_HTML, stats_html,     tree_cards_html, include_js=True)
    pdf_content  = _build_crop_html(_CSS_PDF,  stats_html_pdf, tree_cards_html, include_js=False)

    # ── Plain-text version ──────────────────────────────────
    txt_content = f"تقرير محصول {crop_name}\nالتاريخ: {date_str}\n\n"
    for tid, rep in reports.items():
        txt_content += f"{'='*60}\nشجرة رقم {tid}\n{'='*60}\n{rep}\n\n"

    return _write_files(
        html_content, f"{base}.html",
        f"{base}.txt", txt_content,
        f"{base}.pdf",
        pdf_content=pdf_content,
    )