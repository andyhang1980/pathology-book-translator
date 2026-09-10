# Pathology Book Translator

病理学专业书籍端到端翻译交付系统。从英文结构化数据到出版级中文+双语Word文档，一键完成。

## Features

- **多模型API池**: 智谱GLM / 小米MiMo，自动轮换密钥，超时重试
- **三阶段校对**: 术语一致性 → 完整性检查 → 自动修复
- **出版级排版**: 精确图片比例、纯黑正文、首行缩进、表格无错位
- **双语对照**: 中英段落交替排列，方便专业读者对照阅读
- **图片压缩**: 300DPI印刷质量，90%压缩率（1.8GB → 180MB）
- **断点续传**: 自动跳过已翻译的文件

## Quick Start

```bash
# 安装依赖
pip install Pillow lxml

# 一键全流程
python3 scripts/pipeline.py \
  --input /path/to/cache/ \
  --images /path/to/images/ \
  --output-dir /path/to/output/ \
  --title "WHO肿瘤分类 软组织与骨肿瘤"
```

## Workflow

```
Phase 1: 翻译 (translate.py)
  ├── 英文cache → 批量并发翻译（8 workers）
  ├── 多模型轮换（GLM-4-Flash-250414 / glm-4-flash / mimo-v2.5）
  └── 输出: cache_zh/

Phase 2: 校对 (proofread.py)
  ├── Dict格式标题修复
  ├── 未翻译段落检测
  ├── 非标准术语纠正（冬眠瘤、弹力纤维瘤等）
  └── 输出: cache_zh_final/

Phase 3: 构建Word (build_docx.py)
  ├── 中文版: 封面 + 目录 + 正文 + 封底
  ├── 双语版: EN+ZH段落交替
  └── 输出: 原版/*.docx

Phase 4: 压缩 (compress.py)
  ├── 图片最大800×700像素（300DPI）
  ├── JPEG质量80%
  └── 输出: 压缩版/*.docx

Phase 5: 验证 (verify.py)
  ├── ZIP/XML完整性
  ├── 图片比例（cx/cy vs 原始w/h）
  ├── 封面封底目录检查
  └── Word打开测试
```

## Output Structure

```
output/
├── 原版/
│   ├── 书名_英文_交付版.docx    (~1.8GB)
│   ├── 书名_中文_交付版.docx    (~1.8GB)
│   └── 书名_双语_交付版.docx    (~1.8GB)
└── 压缩版/
    ├── 书名_英文_交付版.docx    (~180MB)
    ├── 书名_中文_交付版.docx    (~180MB)
    └── 书名_双语_交付版.docx    (~180MB)
```

## Configuration

### API Pool

Create `config/api_pool.json`:

```json
[
  {"key": "your_zhipu_key", "model": "GLM-4-Flash-250414", "endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions"},
  {"key": "your_xiaomi_key", "model": "mimo-v2.5", "endpoint": "https://api.xiaomimimo.com/v1/chat/completions"}
]
```

### Terminology

Edit `references/glossary_pathology.md` to add domain-specific terms.

## Individual Scripts

```bash
# 只翻译
python3 scripts/translate.py --input cache/ --output cache_zh/

# 只校对
python3 scripts/proofread.py --en-dir cache/ --zh-dir cache_zh/ --output cache_final/

# 只构建Word
python3 scripts/build_docx.py --cache cache_zh/ --images images/ --output book.docx

# 只压缩
python3 scripts/compress.py --input 原版/ --output 压缩版/

# 只验证
python3 scripts/verify.py --files 原版/ 压缩版/
```

## DOCX Format Specification

| Element | Specification |
|---------|---------------|
| Page | A4 (11906×16838 twips), margins 720 |
| Body font | Times New Roman + 宋体, 11pt, first-line indent 2 chars |
| Headings | Arial + 黑体, centered, bold, pure black |
| Images | Table 10466 twips, aspect-fit, max 3.10×2.70 inches |
| Colors | All pure black 000000, no gray/blue |

## Requirements

- Python 3.8+
- Pillow (PIL)
- lxml
- 7-Zip (for cover/backcover generation)

## License

MIT

## Credits

- [cuimao-translator](https://github.com/Cuimao777/cuimao-translator) — Three-stage refinement workflow
- [english-paper-translator](https://github.com/Casperpan/english-paper-translator) — Translation-as-rewriting philosophy
- [lazy-english-reader](https://github.com/designservice/lazy-english-reader.skill) — Multi-product architecture
- [who-bilingual-ebook](https://github.com/andyhang1980/who-bilingual-ebook) — WHO BlueBooksOnline scraper
