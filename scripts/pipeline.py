# -*- coding: utf-8 -*-
"""一键全流程：翻译→校对→构建→压缩→验证"""
import os, sys, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run(args):
    t0 = time.time()
    base = os.path.dirname(os.path.abspath(__file__))

    # Phase 1: 翻译
    print('='*60)
    print('Phase 1: 翻译')
    print('='*60)
    zh_dir = os.path.join(args.output_dir, 'cache_zh')
    os.makedirs(zh_dir, exist_ok=True)
    os.system(f'python3 "{base}/translate.py" --input "{args.input}" --output "{zh_dir}" --workers {args.workers}')
    print(f'翻译完成: {zh_dir}')

    # Phase 2: 校对
    if not args.skip_proofread:
        print('\n' + '='*60)
        print('Phase 2: 校对')
        print('='*60)
        final_dir = os.path.join(args.output_dir, 'cache_zh_final')
        os.makedirs(final_dir, exist_ok=True)
        os.system(f'python3 "{base}/proofread.py" --en-dir "{args.input}" --zh-dir "{zh_dir}" --output "{final_dir}"')
        zh_dir = final_dir
        print(f'校对完成: {zh_dir}')
    else:
        print('\n跳过校对')

    # Phase 3: 构建Word
    print('\n' + '='*60)
    print('Phase 3: 构建Word')
    print('='*60)
    orig_dir = os.path.join(args.output_dir, '原版')
    os.makedirs(orig_dir, exist_ok=True)

    # 中文版
    zh_docx = os.path.join(orig_dir, f'{args.title}_中文_交付版.docx')
    os.system(f'python3 "{base}/build_docx.py" --cache "{zh_dir}" --images "{args.images}" --output "{zh_docx}" --title "{args.title}"')

    # 双语版
    if not args.skip_bilingual:
        bi_dir = os.path.join(args.output_dir, 'cache_bi')
        os.makedirs(bi_dir, exist_ok=True)
        os.system(f'python3 "{base}/build_bi_cache.py" --en-dir "{args.input}" --zh-dir "{zh_dir}" --output "{bi_dir}"')
        bi_docx = os.path.join(orig_dir, f'{args.title}_双语_交付版.docx')
        os.system(f'python3 "{base}/build_docx.py" --cache "{bi_dir}" --images "{args.images}" --output "{bi_docx}" --title "{args.title}" --bilingual')

    # Phase 4: 压缩
    if not args.skip_compress:
        print('\n' + '='*60)
        print('Phase 4: 图片压缩')
        print('='*60)
        comp_dir = os.path.join(args.output_dir, '压缩版')
        os.system(f'python3 "{base}/compress.py" --input "{orig_dir}" --output "{comp_dir}"')

    # Phase 5: 验证
    print('\n' + '='*60)
    print('Phase 5: 验证')
    print('='*60)
    os.system(f'python3 "{base}/verify.py" --files "{orig_dir}"')

    elapsed = (time.time() - t0) / 60
    print(f'\n{"="*60}')
    print(f'完成! 总耗时: {elapsed:.1f} 分钟')
    print(f'原版: {orig_dir}')
    if not args.skip_compress:
        print(f'压缩版: {os.path.join(args.output_dir, "压缩版")}')
    print(f'{"="*60}')


def main():
    p = argparse.ArgumentParser(description='病理学翻译一键全流程')
    p.add_argument('--input', required=True, help='英文cache目录')
    p.add_argument('--images', required=True, help='图片目录')
    p.add_argument('--output-dir', required=True, help='输出目录')
    p.add_argument('--title', default='病理学', help='文档标题')
    p.add_argument('--workers', type=int, default=8, help='翻译并发数')
    p.add_argument('--skip-proofread', action='store_true', help='跳过校对')
    p.add_argument('--skip-bilingual', action='store_true', help='跳过双语版')
    p.add_argument('--skip-compress', action='store_true', help='跳过压缩')
    args = p.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    run(args)


if __name__ == '__main__':
    main()
