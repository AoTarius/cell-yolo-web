
#!/usr/bin/env python3
"""
将图像序列组合成视频

========================================
使用说明
========================================

基本用法：
    python3 convert.py --input /path/to/images

指定帧率：
    python3 convert.py --input /path/to/images --fps 10

指定输出文件名：
    python3 convert.py --input /path/to/images --output my_video.mp4

完整参数：
    python3 convert.py --input /path/to/images --output output.mp4 --fps 10 --pattern "t*.tif"

========================================
参数说明
========================================

    --input, -i      输入图像目录（必需）
                    示例: --input /path/to/images 或 -i /path/to/images

    --output, -o     输出视频路径（可选）
                    如果不指定，自动生成时间戳文件名: output/YYYYMMDDhhmmss.mp4
                    示例: --output my_video.mp4 或 -o my_video.mp4

    --fps            帧率（可选，默认: 10）
                    控制视频播放速度
                    示例: --fps 10 表示每秒10帧

    --pattern        图像文件名模式（可选，默认: t*.tif）
                    使用通配符匹配图像文件
                    示例: --pattern "img_*.png" 或 --pattern "*.jpg"

========================================
输出格式
========================================

输出视频保存在 output/ 目录下（或指定路径）
文件格式: MP4
编码器: mp4v

========================================
示例
========================================

1. 转换当前目录下的图片：
    python3 convert.py --input .

2. 转换指定目录，帧率 15：
    python3 convert.py --input /path/to/images --fps 15

3. 转换 PNG 图片序列：
    python3 convert.py --input /path/to/images --pattern "*.png"

4. 指定输出路径：
    python3 convert.py --input /path/to/images --output /tmp/result.mp4

========================================
注意事项
========================================

- 图片文件名必须能按字母顺序排序
- 所有图片应具有相同的分辨率
- 需要 OpenCV 库: pip install opencv-python
- 支持 .tif, .png, .jpg, .jpeg 等常见图片格式
"""

import cv2
from pathlib import Path
from datetime import datetime


def images_to_video(
    images_dir: str,
    output_path: str,
    fps: int = 10,
    pattern: str = "t*.tif"
):
    """
    将图像序列组合成视频

    Args:
        images_dir: 图像目录
        output_path: 输出视频路径
        fps: 帧率
        pattern: 图像文件名模式
    """
    images_dir = Path(images_dir)

    # 获取所有图像文件并排序
    image_files = sorted(images_dir.glob(pattern))

    if not image_files:
        print(f"未找到匹配的图像文件: {images_dir}/{pattern}")
        return

    print(f"找到 {len(image_files)} 张图像")

    # 读取第一张图像获取尺寸
    first_image = cv2.imread(str(image_files[0]))
    if first_image is None:
        print(f"无法读取图像: {image_files[0]}")
        return

    height, width = first_image.shape[:2]

    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # 逐帧写入视频
    for i, image_file in enumerate(image_files):
        img = cv2.imread(str(image_file))
        if img is None:
            print(f"无法读取图像: {image_file}")
            continue

        video_writer.write(img)

        # 显示进度
        if (i + 1) % 10 == 0 or i == len(image_files) - 1:
            print(f"处理进度: {i + 1}/{len(image_files)}")

    video_writer.release()

    # 计算视频时长
    duration = len(image_files) / fps
    print(f"\n视频已保存到: {output_path}")
    print(f"视频信息:")
    print(f"  - 分辨率: {width}x{height}")
    print(f"  - 帧数: {len(image_files)}")
    print(f"  - 帧率: {fps} fps")
    print(f"  - 时长: {duration:.1f} 秒")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="将图像序列组合成视频")
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="输入图像目录（必需）")
    parser.add_argument("--output", "-o", type=str,
                        help="输出视频路径（默认：output/YYYYMMDDhhmmss.mp4）")
    parser.add_argument("--fps", type=int, default=10,
                        help="帧率（默认：10）")
    parser.add_argument("--pattern", type=str, default="t*.tif",
                        help="图像文件名模式（默认：t*.tif）")

    args = parser.parse_args()

    # 获取脚本所在目录
    script_dir = Path(__file__).parent

    # 构建输入路径
    input_dir = Path(args.input)

    # 构建输出路径
    if args.output:
        output_path = Path(args.output)
        # 如果是相对路径，放在 output 目录下
        if not output_path.is_absolute():
            output_path = script_dir / 'output' / output_path
    else:
        # 使用时间戳作为文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = script_dir / 'output' / f"{timestamp}.mp4"

    # 确保 output 目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    images_to_video(
        str(input_dir),
        str(output_path),
        args.fps,
        args.pattern
    )