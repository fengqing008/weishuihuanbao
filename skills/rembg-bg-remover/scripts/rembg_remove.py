#!/usr/bin/env python3
"""
rembg 本地图片去背景/抠图脚本（CPU推理）
"""
import argparse
import sys
import os
from pathlib import Path

# 强制rembg模型走gh-proxy下载（沙箱GitHub直连被墙）
os.environ.setdefault('POOCH_HOME', str(Path.home() / '.rembg' / 'models'))
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')


def get_session(model_name: str):
    """懒加载rembg session（首次调用下载模型）"""
    from rembg import new_session
    return new_session(model_name)


def remove_bg(input_path: str, output_path: str, model_name: str = 'u2netp', alpha_matting: bool = False):
    """单图去背景"""
    from rembg import remove
    from PIL import Image

    session = get_session(model_name)
    img = Image.open(input_path).convert('RGB')
    out_kwargs = {'session': session}
    if alpha_matting:
        out_kwargs.update({'alpha_matting': True, 'alpha_matting_foreground_threshold': 240,
                           'alpha_matting_background_threshold': 10, 'alpha_matting_erode_size': 10})
    result = remove(img, **out_kwargs)
    result.save(output_path)
    return output_path


def batch_remove(input_dir: str, output_dir: str, model_name: str = 'u2netp', ext_list=None):
    """批量去背景"""
    from PIL import Image
    ext_list = ext_list or ['jpg', 'jpeg', 'png', 'webp', 'bmp']
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    exts = {f'.{e.lower()}' for e in ext_list}
    files = sorted([p for p in input_path.rglob('*') if p.suffix.lower() in exts and p.is_file()])
    if not files:
        print(f"[rembg] 输入目录无图片: {input_dir}", file=sys.stderr)
        return []
    print(f"[rembg] 共{len(files)}张图，模型={model_name}")
    results = []
    for i, f in enumerate(files, 1):
        rel = f.relative_to(input_path)
        out = output_path / rel.with_suffix('.png')
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            remove_bg(str(f), str(out), model_name)
            print(f"[rembg] [{i}/{len(files)}] {f.name} -> {out.name}")
            results.append(str(out))
        except Exception as e:
            print(f"[rembg] [{i}/{len(files)}] 失败 {f.name}: {e}", file=sys.stderr)
    return results


def list_models():
    """列出可用模型"""
    from rembg.bg import sessions
    print("[rembg] 可用模型（名称: 大小）:")
    sizes = {'u2netp': '4.7MB', 'u2net': '176MB', 'u2net_human_seg': '176MB',
             'u2net_cloth_seg': '176MB', 'silueta': '4.7MB',
             'isnet-general-use': '168MB', 'isnet-anime': '168MB'}
    for name in sorted(sessions.keys()):
        print(f"  - {name}: {sizes.get(name, '?')}")


def _preflight():
    try:
        import rembg  # noqa: F401
    except Exception as e:
        print("[rembg] 缺少依赖 rembg：%s" % e, file=sys.stderr)
        print("请安装：pip install rembg onnxruntime", file=sys.stderr)
        sys.exit(2)


def main():
    _preflight()
    parser = argparse.ArgumentParser(description="rembg本地图片去背景（CPU推理，免API Key）")
    sub = parser.add_subparsers(dest='cmd', required=True)

    p1 = sub.add_parser('single', help='单图去背景')
    p1.add_argument('input', help='输入图片路径')
    p1.add_argument('output', help='输出PNG路径（透明背景）')
    p1.add_argument('--model', default='u2netp', help='模型：u2netp/u2net/isnet-general-use/u2net_human_seg')
    p1.add_argument('--alpha-matting', action='store_true', help='边缘优化（慢但更精细）')

    p2 = sub.add_parser('batch', help='批量去背景')
    p2.add_argument('input_dir', help='输入目录')
    p2.add_argument('output_dir', help='输出目录')
    p2.add_argument('--model', default='u2netp')
    p2.add_argument('--ext', default='jpg,jpeg,png,webp,bmp', help='扩展名（逗号分隔）')

    sub.add_parser('models', help='列出可用模型')

    args = parser.parse_args()
    try:
        if args.cmd == 'single':
            out = remove_bg(args.input, args.output, args.model, args.alpha_matting)
            print(f"[rembg] OK: {out}")
        elif args.cmd == 'batch':
            exts = [e.strip() for e in args.ext.split(',')]
            results = batch_remove(args.input_dir, args.output_dir, args.model, exts)
            print(f"[rembg] 完成{len(results)}张")
        elif args.cmd == 'models':
            list_models()
    except Exception as e:
        print(f"[rembg] 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
