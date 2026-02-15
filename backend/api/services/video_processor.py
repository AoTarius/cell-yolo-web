"""
视频处理服务
将上传的视频分解为帧，调用 YOLO 模型进行细胞分割和追踪，返回 JSON 结果
"""

import os
import cv2
import json
import sys
import subprocess
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from datetime import datetime

# 添加模型路径到 sys.path
# 从 web/backend/api/services/video_processor.py 到 backend 目录需要 3 个 parent
BACKEND_DIR = Path(__file__).parent.parent.parent
MODEL_DIR = BACKEND_DIR / 'models'
YOLO_SOURCE_DIR = BACKEND_DIR  # YOLO 源码在 backend 目录下
MODEL_NAME = 'best.pt' # 选择模型名称，从models文件夹挑选

# 添加 backend 目录到 sys.path，以便导入 ultralytics
sys.path.insert(0, str(YOLO_SOURCE_DIR))


class VideoProcessor:
    """视频处理器"""

    def __init__(self, model_path: str, output_base_dir: str):
        self.model_path = model_path
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)

    def extract_frames(self, video_path: str, output_dir: Path, progress_callback: Optional[Callable[[int, int], None]] = None) -> int:
        """
        将视频分解为帧图像

        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            progress_callback: 进度回调函数 (current_frame, total_frames)

        Returns:
            提取的帧数
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")

        # 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        output_dir.mkdir(parents=True, exist_ok=True)

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 保存帧为 PNG
            frame_filename = output_dir / f"t{frame_count:04d}.png"
            cv2.imwrite(str(frame_filename), frame)

            frame_count += 1

            # 调用进度回调
            if progress_callback:
                progress_callback(frame_count, total_frames)

        cap.release()

        return frame_count

    def process_video(
        self,
        video_path: str,
        task_id: str,
        conf: float = 0.3,
        imgsz: int = 1024,
        fps: int = 10,
        progress_callback: Optional[Callable[[str, int, Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        处理视频：分解帧 -> 调用模型 -> 生成 JSON 结果

        Args:
            video_path: 视频文件路径
            task_id: 任务ID
            conf: 置信度阈值
            imgsz: 图像尺寸
            fps: 输出视频帧率
            progress_callback: 进度回调函数 (stage, progress, data)

        Returns:
            处理结果 JSON
        """
        task_dir = self.output_base_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # 阶段1: 分解视频为帧
        if progress_callback:
            progress_callback('extracting', 0, {'message': '开始分解视频...'})

        frames_dir = task_dir / 'frames'
        total_frames = self.extract_frames(
            video_path,
            frames_dir,
            progress_callback=lambda current, total: progress_callback(
                'extracting',
                int(current / total * 100) if total > 0 else 0,
                {'message': f'分解帧 {current}/{total}'}
            )
        )

        if progress_callback:
            progress_callback('extracting', 100, {'message': f'视频分解完成，共 {total_frames} 帧'})

        # 阶段2: 调用 convert_results.py
        if progress_callback:
            progress_callback('processing', 0, {'message': '开始 YOLO 推理和追踪...'})

        # 构建输出目录
        output_dir = task_dir / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)

        # 构建命令
        convert_script = Path(__file__).parent / 'convert_results.py'
        cmd = [
            sys.executable,
            str(convert_script),
            '--model', self.model_path,
            '--source', str(frames_dir),
            '--output', str(output_dir),
            '--conf', str(conf),
            '--imgsz', str(imgsz),
            '--fps', str(fps)
        ]

        # 运行命令
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(YOLO_SOURCE_DIR)
        )

        # 读取输出以更新进度
        for line in process.stdout:
            line = line.strip()
            print(f"[YOLO] {line}")

            # 解析进度信息
            if line.startswith("PROGRESS:"):
                try:
                    # 格式: "PROGRESS: 45/100|45"
                    progress_info = line.split("|")
                    if len(progress_info) >= 2:
                        frame_info = progress_info[0].split(":")[1].strip()  # "45/100"
                        percentage = int(progress_info[1])  # 45

                        current_frame, total_frames = map(int, frame_info.split("/"))

                        if progress_callback:
                            progress_callback('processing', percentage, {
                                'message': f'处理帧 {current_frame}/{total_frames}',
                                'current_frame': current_frame,
                                'total_frames': total_frames
                            })
                except (ValueError, IndexError) as e:
                    print(f"解析进度信息失败: {e}")
            elif progress_callback:
                # 默认进度（兼容未修改的版本）
                progress_callback('processing', 50, {'message': f'YOLO 处理中...'})

        process.wait()

        if process.returncode != 0:
            error_output = process.stderr.read()
            raise RuntimeError(f"YOLO 处理失败: {error_output}")

        if progress_callback:
            progress_callback('processing', 100, {'message': 'YOLO 处理完成'})

        # 阶段3: 生成 JSON 结果
        if progress_callback:
            progress_callback('packaging', 0, {'message': '生成 JSON 结果...'})

        result = self._generate_json_result(
            task_id,
            output_dir,
            total_frames,
            video_path,
            progress_callback=lambda prog: progress_callback('packaging', prog, {'message': '生成 JSON 结果...'})
        )

        if progress_callback:
            progress_callback('packaging', 100, {'message': '处理完成'})

        return result

    def _generate_json_result(
        self,
        task_id: str,
        output_dir: Path,
        total_frames: int,
        video_path: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Dict[str, Any]:
        """
        生成 JSON 格式的处理结果

        Args:
            task_id: 任务ID
            output_dir: YOLO 输出目录
            total_frames: 总帧数
            video_path: 原始视频路径
            progress_callback: 进度回调函数

        Returns:
            JSON 结果字典
        """
        # 读取 tracking_summary.txt
        summary_path = output_dir / 'tracking_summary.txt'
        summary = self._parse_summary(summary_path)

        # 读取 tracking_results_mot.txt
        mot_path = output_dir / 'tracking_results_mot.txt'
        tracking_data = self._parse_mot_file(mot_path)

        # 读取每帧的 label 文件
        labels_dir = output_dir / 'labels'
        frame_labels = self._parse_labels(labels_dir)

        # 统计信息
        cell_count = len(tracking_data) if tracking_data else 0

        # 获取标注视频路径
        annotated_video_path = output_dir / 'tracking_result.mp4'
        annotated_video_url = f"/api/video/{task_id}"

        result = {
            'task_id': task_id,
            'status': 'completed',
            'progress': 100,
            'total_frames': total_frames,
            'cell_count': cell_count,
            'annotated_video_path': str(annotated_video_path),
            'annotated_video_url': annotated_video_url,
            'original_video_path': video_path,
            'created_at': datetime.now().isoformat(),
            'summary': summary,
            'tracking_data': tracking_data,
            'frame_labels': frame_labels
        }

        # 保存 JSON 文件
        json_path = self.output_base_dir / task_id / 'result.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        if progress_callback:
            progress_callback(100)

        return result

    def _parse_summary(self, summary_path: Path) -> Dict[str, Any]:
        """解析 tracking_summary.txt"""
        if not summary_path.exists():
            return {}

        summary = {}
        with open(summary_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith('-'):
                continue

            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # 尝试转换为数字
                if '(' in value:
                    # 复杂值，保留字符串
                    summary[key] = value
                elif value.isdigit():
                    summary[key] = int(value)
                elif value.replace('.', '').isdigit():
                    summary[key] = float(value)
                else:
                    summary[key] = value

        return summary

    def _parse_mot_file(self, mot_path: Path) -> list:
        """解析 tracking_results_mot.txt"""
        if not mot_path.exists():
            return []

        tracking_data = []
        with open(mot_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split(',')
            if len(parts) >= 9:
                tracking_data.append({
                    'frame': int(parts[0]),
                    'track_id': int(parts[1]),
                    'bb_left': float(parts[2]),
                    'bb_top': float(parts[3]),
                    'bb_width': float(parts[4]),
                    'bb_height': float(parts[5]),
                    'conf': float(parts[6]),
                    'class': int(parts[7]),
                    'visibility': float(parts[8])
                })

        return tracking_data

    def _parse_labels(self, labels_dir: Path) -> Dict[str, list]:
        """解析每帧的 label 文件"""
        if not labels_dir.exists():
            return {}

        frame_labels = {}

        for label_file in labels_dir.glob('*.txt'):
            frame_name = label_file.stem
            labels = []

            with open(label_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 6:
                        labels.append({
                            'track_id': int(parts[0]),
                            'class': int(parts[1]),
                            'x_center': float(parts[2]),
                            'y_center': float(parts[3]),
                            'width': float(parts[4]),
                            'height': float(parts[5])
                        })

            frame_labels[frame_name] = labels

        return frame_labels


def get_video_processor():
    """获取视频处理器实例"""
    model_path = str(MODEL_DIR / MODEL_NAME)
    output_base_dir = Path(__file__).parent.parent.parent / 'media' / 'tasks'
    return VideoProcessor(model_path, str(output_base_dir))