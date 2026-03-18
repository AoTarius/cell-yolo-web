import json
from backend.api.models import Task, Cell
from django.db import transaction
import math
from collections import defaultdict
from pathlib import Path
import shutil
import os

def calculate_area(bb_width, bb_height):
    """计算面积"""
    return bb_width * bb_height

def calculate_center(bb_left, bb_top, bb_width, bb_height):
    """计算中心点"""
    return {
        'cx': bb_left + bb_width / 2,
        'cy': bb_top + bb_height / 2
    }

def calculate_shape_metrics(bb_width, bb_height):
    """计算形态指标"""
    perimeter = 2 * (bb_width + bb_height)
    aspect_ratio = bb_width / bb_height if bb_height > 0 else 0
    circularity = (4 * math.pi * calculate_area(bb_width, bb_height)) / (perimeter ** 2) if perimeter > 0 else 0
    return {
        'perimeter': perimeter,
        'aspect_ratio': aspect_ratio,
        'circularity': circularity
    }

def calculate_motion_metrics(track_data):
    """计算运动指标"""
    metrics = []
    for i in range(1, len(track_data)):
        prev = track_data[i - 1]
        curr = track_data[i]
        vx = curr['center']['cx'] - prev['center']['cx']
        vy = curr['center']['cy'] - prev['center']['cy']
        distance = math.sqrt(vx ** 2 + vy ** 2)
        metrics.append({
            'vx': vx,
            'vy': vy,
            'distance': distance
        })
    return metrics

def process_tracking_data(tracking_data, total_frames):
    """
    处理 tracking_data，计算额外字段并返回处理后的数据。
    """
    processed_cells = []
    track_groups = defaultdict(list)

    for item in tracking_data:
        # 计算基础指标
        area = calculate_area(item['bb_width'], item['bb_height'])
        center = calculate_center(item['bb_left'], item['bb_top'], item['bb_width'], item['bb_height'])
        shape_metrics = calculate_shape_metrics(item['bb_width'], item['bb_height'])

        # 分组轨迹数据
        track_groups[item['track_id']].append({
            'frame': item['frame'],
            'center': center
        })

        # 构造处理后的数据
        processed_cells.append({
            'frame': item['frame'],
            'track_id': item['track_id'],
            'bb_left': item['bb_left'],
            'bb_top': item['bb_top'],
            'bb_width': item['bb_width'],
            'bb_height': item['bb_height'],
            'conf': item['conf'],
            'class_id': item['class'],
            'area': area,
            'center': center,
            'metrics_json': {
                'shape': shape_metrics
            }
        })

    # 计算运动指标
    for track_id, track_data in track_groups.items():
        motion_metrics = calculate_motion_metrics(track_data)
        for i, metric in enumerate(motion_metrics):
            processed_cells.append({
                'track_id': track_id,
                'frame': track_data[i + 1]['frame'],
                'metrics_json': {
                    'motion': metric
                }
            })

    return processed_cells

def parse_json_data(json_path):
    """
    解析 JSON 文件，提取 tracking_data 和任务相关信息。
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 提取任务信息
    task_info = {
        'task_id': data['task_id'],
        'status': data['status'],
        'progress': data['progress'],
        'video_id': None,  # 需外部补充
        'user_id': None,   # 需外部补充
        'fps': None,       # 需外部补充
        'task_name': None, # 需外部补充
        'error_message': None, # 需外部补充
        'imgsz': None,     # 需外部补充
        'conf': None       # 需外部补充
    }

    # 提取并处理 tracking_data
    tracking_data = data.get('tracking_data', [])
    processed_cells = process_tracking_data(tracking_data, task_info['progress'])

    return task_info, processed_cells

def save_to_database(cells):
    """
    将解析后的数据存入 Cells 表。
    """
    try:
        # 批量插入 Cell 数据
        db_cells = []
        for cell in cells:
            db_cells.append(Cell(
                frame=cell['frame'],
                track_id=cell['track_id'],
                bb_left=cell['bb_left'],
                bb_top=cell['bb_top'],
                bb_width=cell['bb_width'],
                bb_height=cell['bb_height'],
                conf=cell['conf'],
                class_id=cell['class_id'],
                metrics_json=cell['metrics_json']
            ))

        with transaction.atomic():
            Cell.objects.bulk_create(db_cells)

        print(f"成功存入 {len(db_cells)} 条 Cell 数据！")

    except Exception as e:
        print(f"存入 Cells 表时发生错误: {e}")

def clear_temp_files():
    """清空 temp_files 文件夹中的内容"""
    temp_files_path = Path(__file__).parent / 'temp_files'
    for file in temp_files_path.iterdir():
        if file.is_file():
            file.unlink()
        elif file.is_dir():
            shutil.rmtree(file)

def process_and_save(json_path):
    """
    主函数：解析 JSON 文件并存入 Cells 表。
    """
    task_info, cells = parse_json_data(json_path)
    save_to_database(cells)

    # 清空 temp_files 目录
    clear_temp_files()

if __name__ == "__main__":
    json_file_path = Path(__file__).parent / 'temp_files' / 'result.json'
    process_and_save(json_file_path)
    clear_temp_files()