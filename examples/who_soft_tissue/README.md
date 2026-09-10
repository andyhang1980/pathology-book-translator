# WHO软组织与骨肿瘤（第6版）翻译项目

## 项目概况

- **书籍**: WHO Classification of Tumours, 6th Edition, Volume 87: Soft Tissue and Bone Tumours
- **来源**: [tumourclassification.iarc.who.int](https://tumourclassification.iarc.who.int)
- **章节**: 242章（241内容章 + 1前言）
- **图片**: 1464张

## 翻译结果

| 文件 | 大小 | 说明 |
|------|------|------|
| 原版/WHO_软组织与骨肿瘤_英文_交付版.docx | 1847 MB | 网站原文 |
| 原版/WHO_软组织与骨肿瘤_中文_交付版.docx | 1847 MB | 出版级精校译文 |
| 原版/WHO_软组织与骨肿瘤_双语_交付版.docx | 1847 MB | 英中段落交替 |
| 压缩版/WHO_软组织与骨肿瘤_英文_交付版.docx | 183 MB | 300DPI印刷质量 |
| 压复版/WHO_软组织与骨肿瘤_中文_交付版.docx | 183 MB | 300DPI印刷质量 |
| 压缩版/WHO_软组织与骨肿瘤_双语_交付版.docx | 184 MB | 300DPI印刷质量 |

## 翻译参数

- **模型**: GLM-4-Flash-250414 / glm-4-flash / mimo-v2.5
- **并发**: 8 workers
- **批量**: 8条/请求
- **API请求**: 2356次，0失败

## 校对结果

- 4720条术语修正
- 81条dict格式标题修复
- 1549条图片下诊断翻译
- 34条符号修正（mm²、～、≤、≥）

## 复现

```bash
# 安装依赖
pip install Pillow lxml

# 一键全流程
python3 scripts/pipeline.py \
  --input /path/to/cache/ \
  --images /path/to/images/ \
  --output-dir output/ \
  --title "WHO软组织与骨肿瘤"
```
