"""
视频处理服务
将上传的视频分解为帧，调用 YOLO 模型进行细胞分割和追踪，返回 JSON 结果
"""

import os
import cv2
import json
import sys
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional, Dict, Any, Tuple
from datetime import datetime


# 线程标识辅助函数
def get_thread_prefix(task_id: str = None):
    """获取线程标识前缀，格式: [task_id|T线程ID] 或 [T线程ID]（带颜色）"""
    thread_id = f"T{threading.current_thread().ident}"
    # ANSI 颜色码
    BLUE = '\033[94m'      # 亮蓝色
    CYAN = '\033[96m'      # 青色
    RESET = '\033[0m'      # 重置颜色

    if task_id:
        return f"{BLUE}[{task_id}|{CYAN}{thread_id}{BLUE}]{RESET}"
    return f"{BLUE}[{CYAN}{thread_id}{BLUE}]{RESET}"

# 添加模型路径到 sys.path
# 从 web/backend/api/services/video_processor.py 到 backend 目录需要 3 个 parent
BACKEND_DIR = Path(__file__).parent.parent.parent
MODEL_DIR = BACKEND_DIR / 'models'
YOLO_SOURCE_DIR = BACKEND_DIR  # YOLO 源码在 backend 目录下
MODEL_NAME = 'best_split.pt' # 选择模型名称，从models文件夹挑选

# 添加 backend 目录到 sys.path，以便导入 ultralytics
sys.path.insert(0, str(YOLO_SOURCE_DIR))


class VideoProcessor:
    """视频处理器"""

    def __init__(self, model_path: str, output_base_dir: str):
        self.model_path = model_path
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)

    def extract_frames(self, video_path: str, output_dir: Path, progress_callback: Optional[Callable[[int, int], None]] = None) -> Tuple[int, float]:
        """
        将视频分解为帧图像

        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            progress_callback: 进度回调函数 (current_frame, total_frames)

        Returns:
            (提取的帧数, 视频时长秒数)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")

        # 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        video_duration = total_frames / video_fps if video_fps > 0 else 0

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

        return frame_count, video_duration

    def process_video(
        self,
        video_path: str,
        task_id: str,
        conf: float = 0.3,
        imgsz: int = 1024,
        fps: int = 10,
        model_path: str = None,
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
            model_path: 模型完整路径
            progress_callback: 进度回调函数 (stage, progress, data)

        Returns:
            处理结果 JSON
        """
        # 如果没有提供 model_path，使用默认路径
        if model_path is None:
            model_path = str(MODEL_DIR / MODEL_NAME)
        task_dir = self.output_base_dir / 'tasks' / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # 阶段1: 分解视频为帧
        if progress_callback:
            progress_callback('extracting', 0, {'message': '开始分解视频...'})

        frames_dir = task_dir / 'frames'
        total_frames, video_duration = self.extract_frames(
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
            '--model', model_path,
            '--source', str(frames_dir),
            '--output', str(output_dir),
            '--conf', str(conf),
            '--imgsz', str(imgsz),
            '--fps', str(fps),
            '--task_id', task_id
        ]

        # 运行命令
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(YOLO_SOURCE_DIR)
        )

        # 读取输出以更新进度
        for line in process.stdout:
            line = line.strip()

            # 解析进度信息
            if line.startswith("PROGRESS:"):
                try:
                    # 格式: "PROGRESS: 45/100|45"
                    progress_info = line.split("|")
                    if len(progress_info) >= 2:
                        frame_info = progress_info[0].split(":")[1].strip()  # "45/100"
                        percentage = int(progress_info[1])  # 45

                        current_frame, total_frames = map(int, frame_info.split("/"))

                        # 输出进度信息
                        print(f"{get_thread_prefix(task_id)} 处理帧 {current_frame}/{total_frames} ({percentage}%)")

                        if progress_callback:
                            progress_callback('processing', percentage, {
                                'message': f'处理帧 {current_frame}/{total_frames}',
                                'current_frame': current_frame,
                                'total_frames': total_frames
                            })
                except (ValueError, IndexError) as e:
                    print(f"{get_thread_prefix(task_id)} 解析进度信息失败: {e}")
            else:
                # 其他输出（如加载模型、初始化等）
                print(f"{get_thread_prefix(task_id)} [YOLO] {line}")

        process.wait()

        if process.returncode != 0:
            error_output = process.stderr.read()
            raise RuntimeError(f"YOLO 处理失败: {error_output}")

        if progress_callback:
            progress_callback('processing', 100, {'message': 'YOLO 处理完成'})

        # 阶段3: 生成 JSON 结果
        if progress_callback:
            progress_callback('packaging', 0, {'message': '生成 JSON 结果...'})

        # 从完整路径中提取模型名称（用于显示）
        model_name = Path(model_path).stem if model_path else MODEL_NAME

        result = self._generate_json_result(
            task_id,
            output_dir,
            total_frames,
            video_duration,
            video_path,
            model_name,
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
        video_duration: float,
        video_path: str,
        model_name: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Dict[str, Any]:
        """
        生成 JSON 格式的处理结果

        Args:
            task_id: 任务ID
            output_dir: YOLO 输出目录
            total_frames: 总帧数
            video_duration: 视频时长（秒）
            video_path: 原始视频路径
            model_name: 模型文件名
            progress_callback: 进度回调函数

        Returns:
            JSON 结果字典
        """
        ensure_temp_files_directory()  # 确保 temp_files 文件夹存在

        # 读取 tracking_summary.txt
        summary_path = output_dir / 'tracking_summary.txt'
        summary = self._parse_summary(summary_path)

        # 从 summary 中获取总帧数（更准确）
        actual_total_frames = summary.get('总帧数', total_frames)

        # 读取 tracking_results_mot.txt
        mot_path = output_dir / 'tracking_results_mot.txt'
        tracking_data = self._parse_mot_file(mot_path)

        # 读取每帧的 label 文件
        labels_dir = output_dir / 'labels'
        frame_labels = self._parse_labels(labels_dir)

        # 统计信息
        # 细胞总数应该是唯一 track_id 的数量
        track_ids = set(row['track_id'] for row in tracking_data) if tracking_data else set()
        cell_count = len(track_ids)

        # 生成 cells 数据（从 tracking_data 中提取每个细胞的统计信息）
        cells = []
        if tracking_data:
            # 按 track_id 分组
            from collections import defaultdict
            track_data = defaultdict(list)
            for row in tracking_data:
                track_data[row['track_id']].append(row)

            # 为每个 track_id 生成统计信息
            for track_id in sorted(track_data.keys()):
                frames = track_data[track_id]
                frames.sort(key=lambda x: x['frame'])  # 按帧号排序

                # 计算统计信息
                total_frames_count = len(frames)
                first_frame = frames[0]['frame']
                last_frame = frames[-1]['frame']

                # 计算平均尺寸
                avg_width = sum(f['bb_width'] for f in frames) / total_frames_count
                avg_height = sum(f['bb_height'] for f in frames) / total_frames_count

                # 计算平均置信度
                avg_conf = sum(f['conf'] for f in frames) / total_frames_count

                # 计算平均速度（需要计算相邻帧之间的距离）
                velocities = []
                for i in range(1, len(frames)):
                    prev_frame = frames[i - 1]
                    curr_frame = frames[i]

                    # 计算中心点
                    prev_center_x = prev_frame['bb_left'] + prev_frame['bb_width'] / 2
                    prev_center_y = prev_frame['bb_top'] + prev_frame['bb_height'] / 2
                    curr_center_x = curr_frame['bb_left'] + curr_frame['bb_width'] / 2
                    curr_center_y = curr_frame['bb_top'] + curr_frame['bb_height'] / 2

                    # 计算距离（像素）
                    distance = ((curr_center_x - prev_center_x) ** 2 + (curr_center_y - prev_center_y) ** 2) ** 0.5

                    # 计算速度（像素/帧）
                    velocity = distance / (curr_frame['frame'] - prev_frame['frame'])
                    velocities.append(velocity)

                avg_velocity = sum(velocities) / len(velocities) if velocities else 0

                # 生成帧数据列表（符合前端 CellFrameData 结构）
                frame_list = []
                for i, frame in enumerate(frames):
                    # 计算中心点、面积、速度等信息
                    center_x = frame['bb_left'] + frame['bb_width'] / 2
                    center_y = frame['bb_top'] + frame['bb_height'] / 2
                    area = frame['bb_width'] * frame['bb_height']

                    # 计算速度（相对于前一帧）
                    vx = 0.0
                    vy = 0.0
                    speed = 0.0

                    if i > 0:
                        prev_frame = frame_list[-1]
                        prev_center_x = prev_frame['position']['x']
                        prev_center_y = prev_frame['position']['y']
                        prev_frame_num = prev_frame['frame_number']
                        curr_frame_num = frame['frame']
                        frame_diff = curr_frame_num - prev_frame_num

                        if frame_diff > 0:
                            vx = (center_x - prev_center_x) / frame_diff
                            vy = (center_y - prev_center_y) / frame_diff
                            speed = ((vx ** 2 + vy ** 2) ** 0.5)

                    frame_list.append({
                        'frame_number': frame['frame'],
                        'position': {
                            'x': center_x,
                            'y': center_y
                        },
                        'area': area,
                        'velocity': {
                            'vx': vx,
                            'vy': vy,
                            'speed': speed
                        },
                        'bounding_box': {
                            'x': frame['bb_left'],
                            'y': frame['bb_top'],
                            'width': frame['bb_width'],
                            'height': frame['bb_height']
                        }
                    })

                cells.append({
                    'cell_id': str(track_id),  # 转换为字符串类型
                    'first_frame': first_frame,
                    'last_frame': last_frame,
                    'frame_count': total_frames_count,
                    'avg_width': round(avg_width, 2),
                    'avg_height': round(avg_height, 2),
                    'avg_conf': round(avg_conf, 2),
                    'avg_velocity': round(avg_velocity, 2),
                    'frames': frame_list
                })

        # 获取标注视频路径
        annotated_video_path = output_dir / 'tracking_result.mp4'
        annotated_video_url = f"/api/video/{task_id}"

        result = {
            'task_id': task_id,
            'status': 'completed',
            'progress': 100,
            'total_frames': actual_total_frames,
            'cell_count': cell_count,
            'video_duration': round(video_duration, 2),
            'model_name': model_name,
            'annotated_video_path': str(annotated_video_path),
            'annotated_video_url': annotated_video_url,
            'original_video_path': video_path,
            'created_at': datetime.now().isoformat(),
            'summary': summary,
            'tracking_data': tracking_data,
            'frame_labels': frame_labels,
            'cells': cells
        }

        # 保存 JSON 文件到任务目录
        json_path = self.output_base_dir / 'tasks' / task_id / 'result.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # 额外保存一份 JSON 文件到临时文件夹
        temp_json_path = Path(__file__).parent / 'temp_files' / 'result.json'
        with open(temp_json_path, 'w', encoding='utf-8') as f:
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


def ensure_temp_files_directory():
    """检查并创建 temp_files 文件夹"""
    temp_files_path = Path(__file__).parent / 'temp_files'
    if not temp_files_path.exists():
        temp_files_path.mkdir()