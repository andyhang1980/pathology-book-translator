# -*- coding: utf-8 -*-
"""Phase 1: 病理学翻译引擎（批量并发 + 多模型轮换）"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_pool import APIPool

SYSTEM = """你是资深病理学翻译专家。将英文病理学文本翻译成简体中文，只输出译文。

规则：
1. 术语用WHO权威译名。抗体名、基因符号、人名保留英文。ICD编码行原样保留。
2. 长句≤25字拆分；"的"≤3/句；全角标点。
3. 每个英文段落必须有对应中文，零漏译。
4. 首次缩写括注中文全称。

已知纠正：嗜睡细胞瘤→冬眠瘤，弹性纤维瘤→弹力纤维瘤，不典型纺锤细胞→非典型梭形细胞，有丝分裂象→核分裂象，恶性纤维组织细胞瘤→未分化多形性肉瘤，血管周细胞瘤/血管外皮瘤→孤立性纤维性肿瘤，纺锤细胞→梭形细胞。"""


def translate_chapter(en_path, zh_path, api):
    en = json.load(open(en_path, encoding='utf-8'))
    texts = []
    index = []

    ct = en.get('chapterTitle', '')
    if ct and not re.search(r'[\u4e00-\u9fff]', ct):
        texts.append(ct); index.append(('title',))

    for hi, h in enumerate(en.get('headings', [])):
        t = h.get('title', '')
        if isinstance(t, str) and re.search(r'[A-Za-z]{3,}', t) and not re.search(r'[\u4e00-\u9fff]', t):
            texts.append(t); index.append(('htitle', hi))
        for ti, txt in enumerate(h.get('texts', [])):
            if isinstance(txt, str) and re.search(r'[A-Za-z]{4,}', txt) and not re.search(r'[\u4e00-\u9fff]', txt):
                texts.append(txt); index.append(('ptext', hi, ti))

    for ai, att in enumerate(en.get('attachments', [])):
        for k in ('diagnosis', 'legend'):
            v = att.get(k, '') or ''
            if isinstance(v, str) and re.search(r'[A-Za-z]{2,}', v) and not re.search(r'[\u4e00-\u9fff]', v):
                texts.append(v); index.append(('att', ai, k))

    if not texts:
        return en

    unique = list(dict.fromkeys(texts))
    trans = api.call_batch(SYSTEM, unique, max_tokens=5000, temperature=0.1)
    t2z = {t: trans.get(t, t) for t in unique}

    zh = json.loads(json.dumps(en))
    for item in index:
        kind = item[0]
        if kind == 'title':
            zh['chapterTitle'] = t2z.get(texts[0], ct)
        elif kind == 'htitle':
            zh['headings'][item[1]]['title'] = t2z.get(texts[index.index(item)], '')
        elif kind == 'ptext':
            hi, ti = item[1], item[2]
            zh['headings'][hi]['texts'][ti] = t2z.get(texts[index.index(item)], '')
        elif kind == 'att':
            ai, k = item[1], item[2]
            zh['attachments'][ai][k] = t2z.get(texts[index.index(item)], '')

    with open(zh_path, 'w', encoding='utf-8') as f:
        json.dump(zh, f, ensure_ascii=False, indent=2)
    return zh


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--config')
    p.add_argument('--workers', type=int, default=8)
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)
    api = APIPool(args.config)
    files = sorted(f for f in os.listdir(args.input) if f.startswith('ch') and f.endswith('.json'))
    print(f'待翻译: {len(files)} 章')

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {}
        for fn in files:
            ez = os.path.join(args.input, fn)
            zz = os.path.join(args.output, fn)
            if os.path.exists(zz) and os.path.getsize(zz) > 200:
                done += 1; continue
            futures[pool.submit(translate_chapter, ez, zz, api)] = fn
        for f in as_completed(futures):
            try: f.result(); done += 1
            except Exception as e: print(f'  错误: {futures[f]}: {e}')
            if done % 20 == 0:
                print(f'  进度: {done}/{len(files)}', flush=True)

    print(f'DONE: {done}/{len(files)}')


if __name__ == '__main__':
    main()
