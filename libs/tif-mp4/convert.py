#!/usr/bin/env python3
"""
将图像序列组合成浏览器兼容的视频
"""

import imageio.v2 as imageio  # 使用 v2 API 避免警告
import numpy as np
from pathlib import Path
from datetime import datetime


def images_to_video(
    images_dir: str,
    output_path: str,
    fps: int = 10,
    pattern: str = "t*.tif"
):
    """
    将图像序列组合成浏览器兼容的 H.264 视频
    """
    images_dir = Path(images_dir)

    image_files = sorted(images_dir.glob(pattern))

    if not image_files:
        print(f"未找到匹配的图像文件: {images_dir}/{pattern}")
        return

    print(f"找到 {len(image_files)} 张图像")

    first_image = imageio.imread(str(image_files[0]))
    height, width = first_image.shape[:2]
    print(f"原始图像尺寸: {width}x{height}")

    # 使用 imageio v2 API，设置 macro_block_size=1 避免强制缩放
    # 提高 level 到 4.0 或 5.0 支持更大分辨率
    with imageio.get_writer(
        output_path,
        fps=fps,
        codec='libx264',
        pixelformat='yuv420p',
        quality=8,
        macro_block_size=1,  # 避免强制缩放到16的倍数
        ffmpeg_params=[
            '-preset', 'fast',
            '-movflags', 'faststart',
            '-profile:v', 'high',      # 改为 high 配置文件，支持更高分辨率
            '-level', '4.0',           # 提高级别支持 2588x1942
            '-crf', '23',
            '-vf', 'format=yuv420p'    # 确保像素格式正确
        ]
    ) as writer:

        for image_file in image_files:
            img = imageio.imread(str(image_file))
            img = _preprocess_image(img)
            writer.append_data(img)

    print(f"\n视频已保存到: {output_path}")
    print(f"视频信息:")
    print(f"  - 分辨率: {width}x{height} (原始尺寸，无缩放)")
    print(f"  - 帧数: {len(image_files)}")
    print(f"  - 帧率: {fps} fps")
    print(f"  - 时长: {len(image_files) / fps:.1f} 秒")
    print(f"  - 编码: H.264 (libx264, high profile, level 4.0)")
    print(f"  - 像素格式: yuv420p (浏览器兼容)")


def _preprocess_image(img: np.ndarray) -> np.ndarray:
    """
    预处理图像，确保输出格式为 RGB uint8
    """
    img = np.array(img)

    if len(img.shape) == 2:
        img = np.stack([img, img, img], axis=-1)

    elif img.shape[-1] == 4:
        img = img[:, :, :3]

    if img.dtype != np.uint8:
        if img.max() <= 1.0:
            img = (img * 255).astype(np.uint8)
        else:
            img = (img / img.max() * 255).astype(np.uint8)

    return img


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="将图像序列组合成视频")
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="输入图像目录（必需）")
    parser.add_argument("--output", "-o", type=str,
                        help="输出视频路径")
    parser.add_argument("--fps", type=int, default=10,
                        help="帧率（默认：10）")
    parser.add_argument("--pattern", type=str, default="t*.tif",
                        help="图像文件名模式（默认：t*.tif）")

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    input_dir = Path(args.input)

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = script_dir / 'output' / output_path
    else:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = script_dir / 'output' / f"{timestamp}.mp4"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    images_to_video(
        str(input_dir),
        str(output_path),
        args.fps,
        args.pattern
    )