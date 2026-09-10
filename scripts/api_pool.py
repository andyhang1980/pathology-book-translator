# -*- coding: utf-8 -*-
"""多模型API池：自动轮换密钥，超时重试"""
import json, os, time, threading, urllib.request

class APIPool:
    def __init__(self, config_path=None):
        self.pairs = []
        self.idx = 0
        self.lock = threading.Lock()
        if config_path and os.path.exists(config_path):
            self.pairs = json.load(open(config_path, encoding='utf-8'))
        else:
            # 默认配置
            self.pairs = [
                {'key': '447d9db9322b4cc1a0de2c4b8feacd6e.UPMysAJQnyN2Yoio',
                 'model': 'GLM-4-Flash-250414',
                 'endpoint': 'https://open.bigmodel.cn/api/paas/v4/chat/completions'},
                {'key': 'f86403bd34a54f2a9c146b44dfbda1bf.suuXUTW3bzFNWNmz',
                 'model': 'GLM-4-Flash-250414',
                 'endpoint': 'https://open.bigmodel.cn/api/paas/v4/chat/completions'},
                {'key': '447d9db9322b4cc1a0de2c4b8feacd6e.UPMysAJQnyN2Yoio',
                 'model': 'glm-4-flash',
                 'endpoint': 'https://open.bigmodel.cn/api/paas/v4/chat/completions'},
                {'key': 'sk-c6v6er90nnbwycewgn9xuways28fr9qksqsdson94elp1dau',
                 'model': 'mimo-v2.5',
                 'endpoint': 'https://api.xiaomimimo.com/v1/chat/completions'},
            ]

    def next(self):
        with self.lock:
            p = self.pairs[self.idx % len(self.pairs)]
            self.idx += 1
            return p

    def call(self, system, user, max_tokens=5000, temperature=0.2, timeout=180, retries=4):
        for attempt in range(retries):
            cfg = self.next()
            body = {'model': cfg['model'], 'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user}],
                'temperature': temperature, 'max_tokens': max_tokens}
            if '4.7' in cfg['model']:
                body['thinking'] = {'type': 'disabled'}
            try:
                req = urllib.request.Request(cfg['endpoint'],
                    headers={'Authorization': f'Bearer {cfg["key"]}',
                             'Content-Type': 'application/json'},
                    data=json.dumps(body).encode('utf-8'))
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    resp = json.load(r)
                content = (resp['choices'][0]['message'].get('content') or '').strip()
                if content:
                    return content
            except Exception:
                pass
            time.sleep(min(2 ** attempt, 20))
        return None

    def call_batch(self, system, items, max_tokens=5000, temperature=0.1, timeout=180):
        if not items:
            return {}
        import re
        user = json.dumps(items, ensure_ascii=False)
        for attempt in range(4):
            cfg = self.next()
            body = {'model': cfg['model'], 'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user}],
                'temperature': temperature, 'max_tokens': max_tokens}
            if '4.7' in cfg['model']:
                body['thinking'] = {'type': 'disabled'}
            try:
                req = urllib.request.Request(cfg['endpoint'],
                    headers={'Authorization': f'Bearer {cfg["key"]}',
                             'Content-Type': 'application/json'},
                    data=json.dumps(body).encode('utf-8'))
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    resp = json.load(r)
                content = (resp['choices'][0]['message'].get('content') or '').strip()
                m = re.search(r'\[[\s\S]*?\]', content)
                if m:
                    arr = json.loads(m.group(0))
                    if len(arr) == len(items):
                        return {items[i]: arr[i] for i in range(len(items))}
            except Exception:
                pass
            time.sleep(min(2 ** attempt, 15))
        return {}
