# -*- coding: utf-8 -*-
"""Phase 5: 验证交付（ZIP/XML/比例/封面/目录）"""
import zipfile, re, os, sys
try:
    from lxml import etree
    HAS_LXML = True
except:
    HAS_LXML = False

def verify(path, label):
    print(f'=== {label} ===')
    try:
        z = zipfile.ZipFile(path, 'r')
        bad = z.testzip()
        print(f'  ZIP: {"OK" if not bad else "BAD: " + bad}')
    except Exception as e:
        print(f'  ZIP: ERROR {e}'); return False

    try:
        doc = z.read('word/document.xml')
        if HAS_LXML:
            etree.fromstring(doc)
        print('  XML: OK')
    except Exception as e:
        print(f'  XML: ERROR {e}'); z.close(); return False

    d = doc.decode('utf-8')
    paras = d.count('<w:p>')
    tables = d.count('<w:tbl>')
    exts = re.findall(r'cx="([0-9]+)" cy="([0-9]+)"', d)
    images = len(exts) // 2
    has_cover = 'INTERNATIONAL AGENCY' in d
    has_back = 'WHO肿瘤分类' in d or 'WHO Classification' in d
    has_toc = 'TOC' in d and 'fldChar' in d
    cx_max = max((int(c) for c, y in exts), default=0)
    cy_max = max((int(y) for c, y in exts), default=0)

    print(f'  段落: {paras}  表格: {tables}  图片: {images}')
    print(f'  封面: {"YES" if has_cover else "NO"}  封底: {"YES" if has_back else "NO"}  目录: {"YES" if has_toc else "NO"}')
    if exts:
        print(f'  图片尺寸: cx_max={cx_max/914400:.2f}  cy_max={cy_max/914400:.2f}')

    # 检查颜色
    gray = d.count('w:val="666666"')
    black = d.count('w:val="000000"')
    print(f'  颜色: 灰色={gray}  黑色={black}')

    # 检查缩进
    indent = 'firstLineChars="200"' in d
    print(f'  首行缩进: {"YES" if indent else "NO"}')

    z.close()
    return bad is None

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--files', nargs='+', required=True)
    args = p.parse_args()

    ok = 0; fail = 0
    for path in args.files:
        if os.path.isdir(path):
            for fn in os.listdir(path):
                if fn.endswith('.docx'):
                    fp = os.path.join(path, fn)
                    if verify(fp, fn): ok += 1
                    else: fail += 1
        elif os.path.exists(path):
            if verify(path, os.path.basename(path)): ok += 1
            else: fail += 1
    print(f'\n结果: {ok} 通过, {fail} 失败')

if __name__ == '__main__':
    main()
