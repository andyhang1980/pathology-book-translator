# -*- coding: utf-8 -*-
"""Phase 2: 三阶段校对（术语→完整性→修复）"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_pool import APIPool

KNOWN_FIXES = {
    '嗜睡细胞瘤': '冬眠瘤', '弹性纤维瘤': '弹力纤维瘤',
    '不典型纺锤细胞': '非典型梭形细胞', '有丝分裂象': '核分裂象',
    '纺锤细胞': '梭形细胞', '恶性纤维组织细胞瘤': '未分化多形性肉瘤',
    '血管周细胞瘤': '孤立性纤维性肿瘤', '血管外皮瘤': '孤立性纤维性肿瘤',
}

def to_str(v):
    if isinstance(v, str): return v
    if isinstance(v, dict):
        for val in v.values():
            if isinstance(val, str): return val
    return ''

def fix_dict_formats(ch):
    changed = False
    for h in ch.get('headings', []):
        t = h.get('title', '')
        if isinstance(t, dict):
            for val in t.values():
                if isinstance(val, str): h['title'] = val; changed = True; break
            else: h['title'] = ''; changed = True
        for ti, txt in enumerate(h.get('texts', [])):
            if isinstance(txt, dict):
                for val in txt.values():
                    if isinstance(val, str): h['texts'][ti] = val; changed = True; break
                else: h['texts'][ti] = ''; changed = True
    for att in ch.get('attachments', []):
        for k in ('diagnosis', 'legend'):
            v = att.get(k, '')
            if isinstance(v, dict):
                for val in v.values():
                    if isinstance(val, str): att[k] = val; changed = True; break
                else: att[k] = ''; changed = True
    return changed

def check_terms(ch):
    issues = []
    for hi, h in enumerate(ch.get('headings', [])):
        t = to_str(h.get('title', ''))
        for wrong, right in KNOWN_FIXES.items():
            if wrong in t:
                issues.append(('term', f'h{hi}', wrong, right))
        for ti, txt in enumerate(h.get('texts', [])):
            txt = to_str(txt)
            for wrong, right in KNOWN_FIXES.items():
                if wrong in txt:
                    issues.append(('term', f'h{hi}.t{ti}', wrong, right))
    return issues

def check_completeness(ch):
    issues = []
    ct = to_str(ch.get('chapterTitle', ''))
    if ct and re.search(r'[A-Za-z]{3,}', ct) and not re.search(r'[\u4e00-\u9fff]', ct):
        issues.append(('missing', 'title', ct[:50]))
    for hi, h in enumerate(ch.get('headings', [])):
        t = to_str(h.get('title', ''))
        if t and re.search(r'[A-Za-z]{3,}', t) and not re.search(r'[\u4e00-\u9fff]', t):
            issues.append(('missing', f'h{hi}', t[:50]))
        for ti, txt in enumerate(h.get('texts', [])):
            txt = to_str(txt)
            if txt and re.search(r'[A-Za-z]{4,}', txt) and not re.search(r'[\u4e00-\u9fff]', txt):
                issues.append(('untranslated', f'h{hi}.t{ti}', txt[:50]))
    for ai, att in enumerate(ch.get('attachments', [])):
        diag = to_str(att.get('diagnosis', ''))
        if diag and re.search(r'[A-Za-z]{3,}', diag) and not re.search(r'[\u4e00-\u9fff]', diag):
            issues.append(('missing', f'att{ai}.diag', diag[:40]))
    return issues

def fix_issues(en, zh, issues, api):
    SYSTEM = "你是病理学翻译。将英文翻译成中文，只输出译文。Unknown→未知，None→无，Not applicable→不适用。"
    result = json.loads(json.dumps(zh))
    fix_map = {}
    for kind, loc, val in issues:
        if kind == 'term':
            # 术语替换直接做
            for hi, h in enumerate(result.get('headings', [])):
                t = to_str(h.get('title', ''))
                if val in t:
                    h['title'] = t.replace(val, issues[0][3] if issues else val)
            # 但这里需要wrong→right映射，简化处理
        elif kind in ('missing', 'untranslated'):
            # 收集需要重新翻译的
            if loc == 'title':
                en_ct = to_str(en.get('chapterTitle', ''))
                if en_ct and en_ct not in fix_map:
                    fix_map[en_ct] = None
            elif loc.startswith('h') and '.t' in loc:
                m = re.match(r'h(\d+)\.t(\d+)', loc)
                if m:
                    hi, ti = int(m.group(1)), int(m.group(2))
                    if hi < len(en.get('headings', [])):
                        en_txt = to_str(en['headings'][hi].get('texts', [])[ti:ti+1] and en['headings'][hi]['texts'][ti])
                        if en_txt and en_txt not in fix_map:
                            fix_map[en_txt] = None
            elif loc.startswith('h') and '标题' not in loc:
                m = re.match(r'h(\d+)$', loc)
                if m:
                    hi = int(m.group(1))
                    if hi < len(en.get('headings', [])):
                        en_t = to_str(en['headings'][hi].get('title', ''))
                        if en_t and en_t not in fix_map:
                            fix_map[en_t] = None
            elif loc.startswith('att'):
                m = re.match(r'att(\d+)\.diag', loc)
                if m:
                    ai = int(m.group(1))
                    if ai < len(en.get('attachments', [])):
                        en_d = to_str(en['attachments'][ai].get('diagnosis', ''))
                        if en_d and en_d not in fix_map:
                            fix_map[en_d] = None

    if fix_map:
        vals = list(fix_map.keys())
        trans = api.call_batch(SYSTEM, vals, max_tokens=2000, temperature=0.1)
        for v in vals:
            fix_map[v] = trans.get(v, v)

        # 应用
        for item in issues:
            kind, loc, val = item[0], item[1], item[2]
            if kind in ('missing', 'untranslated'):
                if loc == 'title':
                    en_ct = to_str(en.get('chapterTitle', ''))
                    if en_ct in fix_map:
                        result['chapterTitle'] = fix_map[en_ct]
                elif loc.startswith('h') and '.t' in loc:
                    m = re.match(r'h(\d+)\.t(\d+)', loc)
                    if m:
                        hi, ti = int(m.group(1)), int(m.group(2))
                        en_txt = to_str(en['headings'][hi]['texts'][ti])
                        if en_txt in fix_map and hi < len(result.get('headings', [])):
                            result['headings'][hi]['texts'][ti] = fix_map[en_txt]
                elif loc.startswith('att'):
                    m = re.match(r'att(\d+)\.diag', loc)
                    if m:
                        ai = int(m.group(1))
                        en_d = to_str(en['attachments'][ai].get('diagnosis', ''))
                        if en_d in fix_map and ai < len(result.get('attachments', [])):
                            result['attachments'][ai]['diagnosis'] = fix_map[en_d]

    # 术语替换
    for h in result.get('headings', []):
        t = to_str(h.get('title', ''))
        for wrong, right in KNOWN_FIXES.items():
            if wrong in t: t = t.replace(wrong, right)
        h['title'] = t
        for ti, txt in enumerate(h.get('texts', [])):
            txt = to_str(txt)
            for wrong, right in KNOWN_FIXES.items():
                if wrong in txt: txt = txt.replace(wrong, right)
            h['texts'][ti] = txt
    for att in result.get('attachments', []):
        for k in ('diagnosis', 'legend'):
            v = to_str(att.get(k, ''))
            for wrong, right in KNOWN_FIXES.items():
                if wrong in v: v = v.replace(wrong, right)
            att[k] = v

    return result


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--en-dir', required=True)
    p.add_argument('--zh-dir', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--config')
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)
    api = APIPool(args.config)
    zh_files = sorted(f for f in os.listdir(args.zh_dir) if f.startswith('ch') and f.endswith('.json'))
    print(f'待校对: {len(zh_files)} 章')

    total_fixes = 0
    for i, fn in enumerate(zh_files):
        en_path = os.path.join(args.en_dir, fn)
        zh_path = os.path.join(args.zh_dir, fn)
        out_path = os.path.join(args.output, fn)
        if not os.path.exists(en_path): continue

        en = json.load(open(en_path, encoding='utf-8-sig'))
        zh = json.load(open(zh_path, encoding='utf-8-sig'))

        # Phase 1: 修复dict格式
        fix_dict_formats(zh)

        # Phase 2: 检查
        issues = check_terms(zh) + check_completeness(en, zh)

        # Phase 3: 修复
        if issues:
            zh = fix_issues(en, zh, issues, api)
            total_fixes += len(issues)

        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(zh, f, ensure_ascii=False, indent=2)

        if (i+1) % 20 == 0:
            print(f'  校对: {i+1}/{len(zh_files)}, 修复: {total_fixes}', flush=True)

    print(f'DONE: 校对完成, 修复 {total_fixes} 处')


if __name__ == '__main__':
    main()
