# -*- coding: utf-8 -*-
"""生成双语cache（EN+ZH段落交替）"""
import json, os

def to_str(v):
    if isinstance(v, str): return v
    if isinstance(v, dict):
        for val in v.values():
            if isinstance(val, str): return val
    return ''

def interleave(a_list, b_list):
    out = []
    for a, b in zip(a_list, b_list):
        a, b = to_str(a), to_str(b)
        if a and a.strip(): out.append(a)
        if b and b.strip(): out.append(b)
    return out

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--en-dir', required=True)
    p.add_argument('--zh-dir', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    os.makedirs(args.output, exist_ok=True)

    files = sorted(f for f in os.listdir(args.en_dir) if f.startswith('ch') and f.endswith('.json'))
    made = 0
    for fn in files:
        zh_p = os.path.join(args.zh_dir, fn)
        if not os.path.exists(zh_p) or os.path.getsize(zh_p) < 200: continue
        en = json.load(open(os.path.join(args.en_dir, fn), encoding='utf-8-sig'))
        zh = json.load(open(zh_p, encoding='utf-8-sig'))
        bi = json.loads(json.dumps(en))
        bi['chapterTitle'] = (to_str(zh.get('chapterTitle', '')) + ' ' + to_str(en.get('chapterTitle', ''))).strip()
        for i, hz in enumerate(bi.get('headings', [])):
            he = en['headings'][i] if i < len(en.get('headings', [])) else None
            hzs = zh['headings'][i] if i < len(zh.get('headings', [])) else None
            if he and hzs:
                zt, et = to_str(hzs.get('title', '')), to_str(he.get('title', ''))
                hz['title'] = (zt + ' | ' + et) if (zt and et and zt != et) else (et or zt)
                hz['texts'] = interleave(he.get('texts', []), hzs.get('texts', []))
        for i, a in enumerate(bi.get('attachments', [])):
            if i < len(en.get('attachments', [])) and i < len(zh.get('attachments', [])):
                ae, az = en['attachments'][i], zh['attachments'][i]
                for k in ('legend', 'diagnosis'):
                    ev, zv = to_str(ae.get(k, '')), to_str(az.get(k, ''))
                    a[k] = (zv + ' ' + ev) if (zv and ev and zv != ev) else (zv or ev)
        out = os.path.join(args.output, fn)
        with open(out + '.tmp', 'w', encoding='utf-8') as f:
            json.dump(bi, f, ensure_ascii=False, indent=2)
        os.replace(out + '.tmp', out)
        made += 1
    print(f'双语cache: {made} 章')

if __name__ == '__main__':
    main()
