# -*- coding: utf-8 -*-
"""Phase 3: Word文档构建（中文 + 双语）"""
import json, os, re, struct, zipfile
try:
    from PIL import Image
    HAS_PIL = True
except:
    HAS_PIL = False

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def img_size(path):
    if HAS_PIL:
        try:
            with Image.open(path) as im: return im.size
        except: pass
    try:
        with open(path, 'rb') as f: h = f.read(32)
        if h[:2] == b'\xff\xd8':
            f = open(path, 'rb'); f.read(2)
            while True:
                m = f.read(2)
                if len(m) < 2 or m[0] != 0xFF: break
                if m[1] in (0xC0, 0xC1, 0xC2):
                    f.read(3); w, ht = struct.unpack('>HH', f.read(4)); f.close(); return (w, ht)
                l = struct.unpack('>H', f.read(2))[0]; f.read(l - 2)
            f.close()
        elif h[:8] == b'\x89PNG\r\n\x1a\n':
            return struct.unpack('>II', h[16:24])
    except: pass
    return (100, 100)

def fit(w, h, mw=2834640, mh=2468880):
    if w <= 0 or h <= 0: return mw, mh
    r = min(mw/w, mh/h)
    return int(w*r), int(h*r)

def make_docx(cache_dir, images_dir, output, title, bilingual=False):
    files = sorted(f for f in os.listdir(cache_dir) if f.startswith('ch') and f.endswith('.json'))
    chapters = [json.load(open(os.path.join(cache_dir, f), encoding='utf-8-sig')) for f in files]

    dims = {}
    dp = os.path.join(images_dir, 'dims.json')
    if os.path.exists(dp): dims = json.load(open(dp, encoding='utf-8'))

    body = []
    for ch in chapters:
        ct = ch.get('chapterTitle', '')
        if ct: body.append(f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t xml:space="preserve">{esc(ct)}</w:t></w:r></w:p>')
        for h in ch.get('headings', []):
            lv = h.get('level', 2)
            ht = h.get('headingType', '')
            t = h.get('title', '')
            if isinstance(t, dict):
                for val in t.values():
                    if isinstance(val, str): t = val; break
                else: t = ''
            if lv == 1 or ht == 'disease':
                tag = 'SectionTitle'
            elif lv == 2: tag = 'Heading2'
            elif lv == 3: tag = 'Heading3'
            else: tag = 'SectionTitle'
            if t:
                body.append(f'<w:p><w:pPr><w:pStyle w:val="{tag}"/></w:pPr><w:r><w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>')
            for txt in h.get('texts', []):
                txt = txt if isinstance(txt, str) else str(txt) if txt else ''
                if txt and txt.strip():
                    body.append(f'<w:p><w:pPr><w:pStyle w:val="Normal"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/><w:color w:val="000000"/></w:rPr><w:t xml:space="preserve">{esc(txt)}</w:t></w:r></w:p>')
            for att in h.get('attachments', []):
                fn = att.get('filename', '')
                if not fn: continue
                ip = os.path.join(images_dir, fn)
                if fn in dims: w, ht = dims[fn]
                elif os.path.exists(ip): w, ht = img_size(ip)
                else: w, ht = 800, 600
                cx, cy = fit(w, ht)
                cap = att.get('legend', '') or att.get('diagnosis', '') or ''
                if isinstance(cap, dict):
                    for val in cap.values():
                        if isinstance(val, str): cap = val; break
                    else: cap = ''
                rid = f'rImg_{fn.replace(".", "_").replace(" ", "_")}'
                tbl = '<w:tbl><w:tblPr><w:tblW w:w="10466" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/><w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders><w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="0" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar></w:tblPr>'
                tbl += f'<w:tblGrid><w:gridCol w:w="5233"/><w:gridCol w:w="5233"/></w:tblGrid>'
                tbl += f'<w:tr><w:tc><w:tcPr><w:tcW w:w="10466" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="1" name="Picture"/><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="1" name="Picture"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p></w:tc></w:tr>'
                if cap:
                    tbl += f'<w:tr><w:tc><w:tcPr><w:tcW w:w="10466" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:t xml:space="preserve">{esc(cap)}</w:t></w:r></w:p></w:tc></w:tr>'
                tbl += '</w:tbl>'
                body.append(tbl)

    sz = '18' if bilingual else '21'
    doc = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    doc += '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">\n'
    doc += '<w:body>\n' + '\n'.join(body) + '\n'
    doc += f'<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr>\n'
    doc += '</w:body>\n</w:document>'

    styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/><w:color w:val="000000"/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr><w:pPr><w:spacing w:before="0" w:after="120" w:line="240" w:lineRule="auto"/><w:ind w:firstLineChars="200" w:firstLine="420"/></w:pPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:jc w:val="center"/><w:spacing w:before="240" w:after="120" w:line="360" w:lineRule="auto"/><w:ind w:firstLine="0" w:firstLineChars="0"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="黑体"/><w:b/><w:bCs/><w:color w:val="000000"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:jc w:val="center"/><w:spacing w:before="200" w:after="100" w:line="300" w:lineRule="auto"/><w:ind w:firstLine="0" w:firstLineChars="0"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="黑体"/><w:b/><w:bCs/><w:color w:val="000000"/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:spacing w:before="160" w:after="80" w:line="260" w:lineRule="auto"/><w:ind w:firstLine="0" w:firstLineChars="0"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="黑体"/><w:b/><w:bCs/><w:color w:val="000000"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="SectionTitle"><w:name w:val="Section Title"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:spacing w:before="200" w:after="100" w:line="300" w:lineRule="auto"/><w:ind w:firstLine="0" w:firstLineChars="0"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/><w:b/><w:bCs/><w:color w:val="000000"/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr></w:style>
</w:styles>'''

    ct_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="jpg" ContentType="image/jpeg"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'
    rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
    doc_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    rid = 2; seen = set()
    for ch in chapters:
        for h in ch.get('headings', []):
            for att in h.get('attachments', []):
                fn = att.get('filename', '')
                if fn and fn not in seen:
                    seen.add(fn)
                    doc_rels += f'<Relationship Id="rId{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{fn}"/>'
                    rid += 1
    doc_rels += '</Relationships>'

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct_xml)
        z.writestr('_rels/.rels', rels)
        z.writestr('word/document.xml', doc)
        z.writestr('word/styles.xml', styles)
        z.writestr('word/_rels/document.xml.rels', doc_rels)
        embedded = 0
        for ch in chapters:
            for h in ch.get('headings', []):
                for att in h.get('attachments', []):
                    fn = att.get('filename', '')
                    if fn:
                        ip = os.path.join(images_dir, fn)
                        if os.path.exists(ip):
                            z.write(ip, f'word/media/{fn}'); embedded += 1

    mb = os.path.getsize(output) / (1024*1024)
    print(f'Done: {output} ({mb:.0f} MB, {embedded} images)')


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--cache', required=True)
    p.add_argument('--images', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--title', default='')
    p.add_argument('--bilingual', action='store_true')
    args = p.parse_args()
    make_docx(args.cache, args.images, args.output, args.title, args.bilingual)


if __name__ == '__main__':
    main()
