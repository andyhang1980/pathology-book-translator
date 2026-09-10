# -*- coding: utf-8 -*-
"""Phase 4: 图片压缩（300DPI印刷质量，~90%压缩率）"""
import os, shutil, zipfile, tempfile, sys
from PIL import Image
from io import BytesIO

def compress_img(data, max_w=800, max_h=700, quality=80):
    try:
        img = Image.open(BytesIO(data))
        orig_w, orig_h = img.size
        if len(data) < 300 * 1024:
            return None
        if orig_w > max_w or orig_h > max_h:
            r = min(max_w/orig_w, max_h/orig_h)
            img = img.resize((int(orig_w*r), int(orig_h*r)), Image.LANCZOS)
        if img.mode in ('RGBA', 'P', 'LA'):
            bg = Image.new('RGB', img.size, (255,255,255))
            if img.mode == 'P': img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=quality, optimize=True)
        out = buf.getvalue()
        return out if len(out) < len(data) else None
    except:
        return None

def compress_docx(inp, outp):
    td = tempfile.mkdtemp(prefix='cx_')
    try:
        with zipfile.ZipFile(inp, 'r') as z: z.extractall(td)
        md = os.path.join(td, 'word', 'media')
        if not os.path.exists(md): return 0, 0
        saved = cnt = 0
        for fn in os.listdir(md):
            fp = os.path.join(md, fn)
            if not os.path.isfile(fp): continue
            orig = os.path.getsize(fp)
            if orig < 300*1024: continue
            with open(fp, 'rb') as f: data = f.read()
            new = compress_img(data)
            if new:
                with open(fp, 'wb') as f: f.write(new)
                saved += orig - len(new); cnt += 1
        with zipfile.ZipFile(outp, 'w', zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(td):
                for fn in files:
                    full = os.path.join(root, fn)
                    z.write(full, os.path.relpath(full, td))
        return saved, cnt
    finally:
        shutil.rmtree(td, ignore_errors=True)

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True, help='原版目录')
    p.add_argument('--output', required=True, help='压缩版目录')
    args = p.parse_args()
    os.makedirs(args.output, exist_ok=True)
    for fn in os.listdir(args.input):
        if not fn.endswith('.docx'): continue
        inp = os.path.join(args.input, fn)
        outp = os.path.join(args.output, fn)
        orig = os.path.getsize(inp)/(1024*1024)
        print(f'压缩: {fn} ({orig:.0f} MB)', flush=True)
        saved, cnt = compress_docx(inp, outp)
        new = os.path.getsize(outp)/(1024*1024)
        print(f'  {cnt} 张, {orig:.0f} → {new:.0f} MB ({(1-new/orig)*100:.1f}%)')

if __name__ == '__main__':
    main()
