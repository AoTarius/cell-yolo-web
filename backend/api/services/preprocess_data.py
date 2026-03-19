import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import csv
import math
from collections import defaultdict
from ..models import Cell, Task  

# ==================== 1. 数据类定义 ====================

@dataclass
class RawDetection:
    """原始检测数据 - 对应 JSON 中的单条记录"""
    frame: int
    track_id: int
    bb_left: float
    bb_top: float
    bb_width: float
    bb_height: float
    conf: float
    class_id: int
    visibility: float

@dataclass
class ProcessedCell:
    """处理后的细胞数据 - 对应 Cell 表的一条记录"""
    task_id: str
    frame: int
    track_id: int
    bb_left: float
    bb_top: float
    bb_width: float
    bb_height: float
    conf: float
    class_id: int
    visibility: float
    area: float
    speed: float
    tracking_persistence: float
    metrics_json: Dict[str, Any]

# ==================== 2. 工具函数 ====================

def calculate_area(bb_width: float, bb_height: float) -> float:
    return bb_width * bb_height

def calculate_center(bb_left: float, bb_top: float, bb_width: float, bb_height: float) -> Dict[str, float]:
    return {
        'cx': bb_left + bb_width / 2,
        'cy': bb_top + bb_height / 2
    }

def calculate_shape_metrics(bb_width: float, bb_height: float, area: float) -> Dict[str, float]:
    perimeter = 2 * (bb_width + bb_height)
    aspect_ratio = bb_width / bb_height if bb_height > 0 else 0
    circularity = (4 * math.pi * area) / (perimeter ** 2) if perimeter > 0 else 0
    return {
        'perimeter': perimeter,
        'aspect_ratio': aspect_ratio,
        'circularity': circularity
    }

def calculate_motion_between_frames(prev: Dict, curr: Dict) -> Dict[str, float]:
    prev_center = calculate_center(prev['bb_left'], prev['bb_top'], prev['bb_width'], prev['bb_height'])
    curr_center = calculate_center(curr['bb_left'], curr['bb_top'], curr['bb_width'], curr['bb_height'])
    vx = curr_center['cx'] - prev_center['cx']
    vy = curr_center['cy'] - prev_center['cy']
    distance = math.sqrt(vx ** 2 + vy ** 2)
    return {
        'vx': vx,
        'vy': vy,
        'distance': distance,
        'speed': distance
    }

def calculate_tracking_persistence(total_frames: int, detected_frames: int) -> float:
    """
    计算持续追踪度
    公式: tracking_persistence = detected_frames / total_frames
    """
    return detected_frames / total_frames if total_frames > 0 else 0.0

def calculate_min_track_frames(total_frames: int, min_ratio: float = 0.1) -> int:
    """
    计算最小轨迹帧数阈值
    """
    # 计算比例阈值
    frames_by_ratio = math.ceil(total_frames * min_ratio)
    # 确保最小帧数至少为3
    min_frames = max(3, frames_by_ratio)
    # 对于极短视频的特殊处理
    if total_frames < 10:
        min_frames = max(2, min_frames)  # 进一步放宽

    return min_frames

# ==================== 3. 主处理函数 ====================

def parse_json_data(json_path: Path) -> Tuple[Dict, List[RawDetection], int]:
    """
    解析 JSON 文件，提取任务信息、原始检测数据和总帧数。

    返回:
        - task_info: 任务元信息
        - detections: RawDetection 列表
        - total_frames: 视频的总帧数
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    task_info = {
        'task_id': data.get('task_id'),
        'status': data.get('status'),
        'progress': data.get('progress')
    }

    total_frames = data.get('total_frames', 0)  # 从 JSON 中提取总帧数

    detections = [
        RawDetection(
            frame=item['frame'],
            track_id=item['track_id'],
            bb_left=item['bb_left'],
            bb_top=item['bb_top'],
            bb_width=item['bb_width'],
            bb_height=item['bb_height'],
            conf=item['conf'],
            class_id=item.get('class', 0),
            visibility=item.get('visibility', 1.0)
        )
        for item in data.get('tracking_data', [])
    ]

    return task_info, detections, total_frames

def calculate_msd(trajectory, current_index, tau=1):

    if current_index < tau or current_index >= len(trajectory):
        return 0.0
    
    # 计算当前位置与前tau时刻位置的位移平方
    current = trajectory[current_index]
    previous = trajectory[current_index - tau]
    
    dx = current['bb_left'] - previous['bb_left']
    dy = current['bb_top'] - previous['bb_top']
    
    return dx**2 + dy**2

# 添加角度归一化
def normalize_angle(angle):
    """将角度归一化到[-π, π]区间"""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle

def process_all_detections(detections: List[RawDetection], task_id: str, total_frames: int, 
                          min_track_ratio: float = 0.1) -> List[ProcessedCell]:
    """
    处理所有检测数据，基于总帧数比例过滤短轨迹

    参数:
        detections: 原始检测数据列表
        task_id: 任务ID
        total_frames: 总帧数
        min_track_ratio: 最小轨迹占总帧数的比例阈值，默认0.1（10%）
    """
    # 方案一 基于比例确定筛选细胞至少被追踪的帧数
    # min_track_frames = calculate_min_track_frames(total_frames, min_track_ratio)
    # 方案二 固定最小帧数阈值 3帧可以获得细胞基础的运动数据
    min_track_frames = 3

    track_groups = defaultdict(list)
    for det in detections:
        track_groups[det.track_id].append(det)

    processed_cells = []
    removed_short_tracks = 0
    total_tracks = len(track_groups)

    print(f"视频总帧数: {total_frames}, 最小轨迹阈值: {min_track_frames}帧 ({min_track_ratio*100}%)")

    for track_id, trajectory in track_groups.items():
        # 过滤短轨迹
        if len(trajectory) < min_track_frames:
            removed_short_tracks += 1
            continue  # 跳过短轨迹，不处理

        trajectory.sort(key=lambda x: x.frame)
        detected_frames = len(trajectory)
        tracking_persistence = calculate_tracking_persistence(total_frames, detected_frames)

        # Calculate initial area for Spreading Index
        initial_area = calculate_area(trajectory[0].bb_width, trajectory[0].bb_height) if trajectory else 1.0

        for i, det in enumerate(trajectory):
            area = calculate_area(det.bb_width, det.bb_height)
            center = calculate_center(det.bb_left, det.bb_top, det.bb_width, det.bb_height)
            shape_metrics = calculate_shape_metrics(det.bb_width, det.bb_height, area)

            # Default values for motion metrics
            motion = {
                'vx': 0.0,
                'vy': 0.0,
                'distance': 0.0,
                'migration_speed': 0.0,
                'mean_square_displacement': 0.0,
                'turning_angle': 0.0,
                'persistence_index': tracking_persistence
            }

            if i > 0:
                prev_det = trajectory[i - 1]
                motion_metrics = calculate_motion_between_frames(
                    {
                        'bb_left': prev_det.bb_left,
                        'bb_top': prev_det.bb_top,
                        'bb_width': prev_det.bb_width,
                        'bb_height': prev_det.bb_height
                    },
                    {
                        'bb_left': det.bb_left,
                        'bb_top': det.bb_top,
                        'bb_width': det.bb_width,
                        'bb_height': det.bb_height
                    }
                )
                motion.update({
                    'vx': motion_metrics['vx'],
                    'vy': motion_metrics['vy'],
                    'distance': motion_metrics['distance'],
                    'migration_speed': motion_metrics['speed']
                })

                # Calculate Mean Square Displacement (MSD)
                motion['mean_square_displacement'] = calculate_msd(
                    [{'bb_left': d.bb_left, 'bb_top': d.bb_top, 'bb_width': d.bb_width, 'bb_height': d.bb_height} for d in trajectory],
                    i, tau=1
                )

                # Calculate Turning Angle
                if i >= 2:
                    prev_prev_det = trajectory[i - 2]
                    v1 = calculate_motion_between_frames(
                        {
                            'bb_left': prev_prev_det.bb_left,
                            'bb_top': prev_prev_det.bb_top,
                            'bb_width': prev_prev_det.bb_width,
                            'bb_height': prev_prev_det.bb_height
                        },
                        {
                            'bb_left': prev_det.bb_left,
                            'bb_top': prev_det.bb_top,
                            'bb_width': prev_det.bb_width,
                            'bb_height': prev_det.bb_height
                        }
                    )
                    v2 = motion_metrics
                    angle_diff = math.atan2(v2['vy'], v2['vx']) - math.atan2(v1['vy'], v1['vx'])
                    motion['turning_angle'] = normalize_angle(angle_diff)

            metrics_json = {
                'bbox': {
                    'left': det.bb_left,
                    'top': det.bb_top,
                    'width': det.bb_width,
                    'height': det.bb_height
                },
                'center': center,
                'shape': {
                    'perimeter': shape_metrics['perimeter'],
                    'circularity': shape_metrics['circularity'],
                    'circularity_increment': 0.0,  
                    'aspect_ratio': shape_metrics['aspect_ratio'],
                    'shape_change_rate': 0.0,  
                    'spreading_index': area / initial_area if initial_area > 0 else 1.0,
                    'protrusion_activity_index': 0.0  
                },
                'motion': motion,
                'visibility': det.visibility,
                'cell_class': det.class_id,
                'confidence': det.conf
            }

            if i > 0:
                prev_area = calculate_area(prev_det.bb_width, prev_det.bb_height)
                prev_shape_metrics = calculate_shape_metrics(prev_det.bb_width, prev_det.bb_height, prev_area)
                # 计算突起活动指数（相对变化率）
                if prev_shape_metrics['perimeter'] > 0:
                    protrusion_index = (shape_metrics['perimeter'] - prev_shape_metrics['perimeter']) / prev_shape_metrics['perimeter']
                else:
                    protrusion_index = 0.0

                metrics_json['shape'].update({
                    'circularity_increment': shape_metrics['circularity'] - prev_shape_metrics['circularity'],
                    'shape_change_rate': (area - prev_area) / prev_area if prev_area > 0 else 0.0,
                    'protrusion_activity_index': protrusion_index
                })

            processed_cells.append(ProcessedCell(
                task_id=task_id,
                frame=det.frame,
                track_id=det.track_id,
                bb_left=det.bb_left,
                bb_top=det.bb_top,
                bb_width=det.bb_width,
                bb_height=det.bb_height,
                conf=det.conf,
                class_id=det.class_id,
                visibility=det.visibility,
                area=area,
                speed=motion['migration_speed'],
                tracking_persistence=tracking_persistence,
                metrics_json=metrics_json
            ))

    if removed_short_tracks > 0:
        print(f"过滤掉 {removed_short_tracks}/{total_tracks} 个短轨迹（帧数 < {min_track_frames}）")
        filtered_ratio = removed_short_tracks / total_tracks * 100
        print(f"过滤比例: {filtered_ratio:.1f}%")

    return processed_cells

def save_to_database(cells: List[ProcessedCell]):
    """
    将处理后的细胞数据保存到数据库。

    参数:
        cells: 处理后的细胞数据列表。
    """
    cell_objects = []
    for cell in cells:
        try:
            # 获取对应的 Task 对象
            task = Task.objects.get(task_id=cell.task_id)
            cell_objects.append(
                Cell(
                    task=task,  # 映射到外键字段
                    frame=cell.frame,
                    track_id=cell.track_id,
                    bb_left=cell.bb_left,
                    bb_top=cell.bb_top,
                    bb_width=cell.bb_width,
                    bb_height=cell.bb_height,
                    conf=cell.conf,
                    class_id=cell.class_id,
                    visibility=cell.visibility,
                    area=cell.area,
                    speed=cell.speed,
                    tracking_persistence=cell.tracking_persistence,
                    metrics_json=cell.metrics_json
                )
            )
        except Task.DoesNotExist:
            print(f"错误: 无法找到对应的 Task 对象，task_id={cell.task_id}")

    if cell_objects:
        Cell.objects.bulk_create(cell_objects)
        print(f"成功写入 {len(cell_objects)} 条数据到数据库")

    print(f"成功处理 {len(cells)} 条数据")
    for cell in cells[:3]:
        print(cell)

def save_to_csv(cells: List[ProcessedCell], output_path: Path):
    """
    将处理后的细胞数据保存为 CSV 文件。

    参数:
        cells: 处理后的细胞数据列表。
        output_path: CSV 文件的保存路径。
    """
    with open(output_path, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'task_id', 'frame', 'track_id', 'bb_left', 'bb_top', 'bb_width', 'bb_height',
            'conf', 'class_id', 'visibility', 'area', 'speed', 'tracking_persistence',
            'bbox_left', 'bbox_top', 'bbox_width', 'bbox_height',
            'center_cx', 'center_cy',
            'shape_perimeter', 'shape_circularity', 'shape_circularity_increment',
            'shape_aspect_ratio', 'shape_shape_change_rate', 'shape_spreading_index',
            'shape_protrusion_activity_index',
            'motion_vx', 'motion_vy', 'motion_distance', 'motion_migration_speed',
            'motion_mean_square_displacement', 'motion_turning_angle', 'motion_persistence_index'
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for cell in cells:
            row = {
                'task_id': cell.task_id,
                'frame': cell.frame,
                'track_id': cell.track_id,
                'bb_left': cell.bb_left,
                'bb_top': cell.bb_top,
                'bb_width': cell.bb_width,
                'bb_height': cell.bb_height,
                'conf': cell.conf,
                'class_id': cell.class_id,
                'visibility': cell.visibility,
                'area': cell.area,
                'speed': cell.speed,
                'tracking_persistence': cell.tracking_persistence,
                'bbox_left': cell.metrics_json['bbox']['left'],
                'bbox_top': cell.metrics_json['bbox']['top'],
                'bbox_width': cell.metrics_json['bbox']['width'],
                'bbox_height': cell.metrics_json['bbox']['height'],
                'center_cx': cell.metrics_json['center']['cx'],
                'center_cy': cell.metrics_json['center']['cy'],
                'shape_perimeter': cell.metrics_json['shape']['perimeter'],
                'shape_circularity': cell.metrics_json['shape']['circularity'],
                'shape_circularity_increment': cell.metrics_json['shape']['circularity_increment'],
                'shape_aspect_ratio': cell.metrics_json['shape']['aspect_ratio'],
                'shape_shape_change_rate': cell.metrics_json['shape']['shape_change_rate'],
                'shape_spreading_index': cell.metrics_json['shape']['spreading_index'],
                'shape_protrusion_activity_index': cell.metrics_json['shape']['protrusion_activity_index'],
                'motion_vx': cell.metrics_json['motion']['vx'],
                'motion_vy': cell.metrics_json['motion']['vy'],
                'motion_distance': cell.metrics_json['motion']['distance'],
                'motion_migration_speed': cell.metrics_json['motion']['migration_speed'],
                'motion_mean_square_displacement': cell.metrics_json['motion']['mean_square_displacement'],
                'motion_turning_angle': cell.metrics_json['motion']['turning_angle'],
                'motion_persistence_index': cell.metrics_json['motion']['persistence_index']
            }
            writer.writerow(row)

def process_and_save(json_path: Path, task_id: str, min_track_ratio: float = 0.1):
    """
    主函数: 解析JSON并处理数据

    参数:
        json_path: JSON文件路径
        task_id: 任务ID
        min_track_ratio: 最小轨迹占总帧数的比例，默认0.1（10%）
    """
    task_info, detections, total_frames = parse_json_data(json_path)

    if total_frames == 0:
        print("错误: 无法从JSON数据中提取总帧数。")
        return

    processed_cells = process_all_detections(detections, task_id, total_frames, min_track_ratio)
    save_to_database(processed_cells)

    # 生成 CSV 文件
    output_csv_path = json_path.with_name(f"processed_cells_{task_id}.csv")
    save_to_csv(processed_cells, output_csv_path)

    print(f"任务 {task_id} 的数据处理完成，总帧数: {total_frames}，检测到的轨迹数: {len(set(d.track_id for d in detections))}")
    print(f"处理后的数据已保存为 CSV 文件: {output_csv_path}")

if __name__ == "__main__":
    json_file_path = Path(__file__).parent / 'temp_files' / 'result.json'

    if json_file_path.exists():
        process_and_save(json_file_path, task_id="example_task_id")
    else:
        print(f"文件不存在: {json_file_path}")