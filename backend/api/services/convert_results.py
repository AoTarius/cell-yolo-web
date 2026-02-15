#!/usr/bin/env python3
"""
增强版后处理脚本：重新运行推理，按 track_id 着色掩模 + 生成 PNG + 视频 + TXT 追踪结果
适配旧版 ultralytics v8.0.3 API
"""

import cv2
import os
import sys
import numpy as np
import torch
from pathlib import Path
from tqdm import tqdm
from collections import deque

# 添加路径
# 从 services 目录到 web 目录需要 4 个 parent
WEB_ROOT = Path(__file__).parent.parent.parent.parent
ULTRALYTICS_DIR = WEB_ROOT / "libs" / "ultralytics"
sys.path.insert(0, str(ULTRALYTICS_DIR))

# DeepSORT
SEGMENT_DIR = ULTRALYTICS_DIR / "yolo" / "v8" / "segment"
sys.path.insert(0, str(SEGMENT_DIR))
from deep_sort_pytorch.utils.parser import get_config
from deep_sort_pytorch.deep_sort import DeepSort

from ultralytics import YOLO

# 颜色生成
palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)
data_deque = {}


def compute_color_for_id(track_id):
    """根据 track_id 生成唯一颜色 (BGR)"""
    color = [int((p * (track_id ** 2 - track_id + 1)) % 255) for p in palette]
    return tuple(color)


def init_deepsort():
    """初始化 DeepSORT"""
    cfg_deep = get_config()
    cfg_deep.merge_from_file(str(SEGMENT_DIR / "deep_sort_pytorch/configs/deep_sort.yaml"))

    # 修复 REID_CKPT 路径：将相对路径转换为绝对路径
    reid_ckpt = cfg_deep.DEEPSORT.REID_CKPT
    if not os.path.isabs(reid_ckpt):
        # 如果是相对路径，相对于 ULTRALYTICS_DIR 解析
        reid_ckpt = str(ULTRALYTICS_DIR / reid_ckpt)

    return DeepSort(
        reid_ckpt,
        max_dist=cfg_deep.DEEPSORT.MAX_DIST,
        min_confidence=cfg_deep.DEEPSORT.MIN_CONFIDENCE,
        nms_max_overlap=cfg_deep.DEEPSORT.NMS_MAX_OVERLAP,
        max_iou_distance=cfg_deep.DEEPSORT.MAX_IOU_DISTANCE,
        max_age=cfg_deep.DEEPSORT.MAX_AGE,
        n_init=cfg_deep.DEEPSORT.N_INIT,
        nn_budget=cfg_deep.DEEPSORT.NN_BUDGET,
        use_cuda=True,
        use_reid=getattr(cfg_deep.DEEPSORT, "USE_REID", True)
    )


def xyxy_to_xywh(x1, y1, x2, y2):
    """转换坐标格式"""
    w = x2 - x1
    h = y2 - y1
    cx = x1 + w / 2
    cy = y1 + h / 2
    return cx, cy, w, h


def box_iou(box1, box2):
    """计算 IoU"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0


def draw_mask_by_trackid(img, mask, track_id, alpha=0.5):
    """用 track_id 的颜色绘制掩模"""
    color = compute_color_for_id(track_id)
    H, W = img.shape[:2]

    if hasattr(mask, 'cpu'):
        mask_np = mask.cpu().numpy()
    elif hasattr(mask, 'data'):
        mask_np = mask.data.cpu().numpy()
    else:
        mask_np = np.array(mask)

    if mask_np.ndim > 2:
        mask_np = mask_np.squeeze()

    if mask_np.shape[:2] != (H, W):
        mask_np = cv2.resize(mask_np.astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST)

    binary = mask_np > 0.5

    overlay = img.copy()
    overlay[binary] = color
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


def draw_box_and_label(img, box, track_id, line_thickness=2):
    """绘制边界框和 ID 标签"""
    color = compute_color_for_id(track_id)
    x1, y1, x2, y2 = [int(v) for v in box]

    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness=line_thickness, lineType=cv2.LINE_AA)

    label = f"ID:{track_id}"
    tl = line_thickness
    tf = max(tl - 1, 1)
    t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
    cv2.rectangle(img, (x1, y1 - t_size[1] - 6), (x1 + t_size[0] + 4, y1), color, -1, cv2.LINE_AA)
    cv2.putText(img, label, (x1 + 2, y1 - 4), 0, tl / 3, [255, 255, 255], thickness=tf, lineType=cv2.LINE_AA)


def draw_trajectory(img, track_id, center):
    """绘制轨迹"""
    if track_id not in data_deque:
        data_deque[track_id] = deque(maxlen=64)

    data_deque[track_id].appendleft(center)
    color = compute_color_for_id(track_id)

    for j in range(1, len(data_deque[track_id])):
        if data_deque[track_id][j - 1] is None or data_deque[track_id][j] is None:
            continue
        thickness = int(np.sqrt(64 / float(j + 1)) * 1.5)
        cv2.line(img, data_deque[track_id][j - 1], data_deque[track_id][j], color, max(thickness, 1))


def run_tracking_with_colored_masks(
    model_path: str,
    source_dir: str,
    output_dir: str,
    conf: float = 0.25,
    imgsz: int = 1024,
    fps: int = 10
):
    """
    运行跟踪并按 track_id 着色掩模，同时输出 TXT 追踪结果
    """
    print(f"加载模型: {model_path}")
    model = YOLO(model_path)

    print(f"初始化 DeepSORT...")
    deepsort = init_deepsort()

    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 获取所有图像
    image_files = sorted(source_path.glob("*.tif")) + sorted(source_path.glob("*.png")) + sorted(source_path.glob("*.jpg"))
    if not image_files:
        print(f"未找到图像文件在: {source_dir}")
        return

    print(f"找到 {len(image_files)} 张图像")

    frames = []
    # ========== TXT 输出相关 ==========
    all_tracking_results = []   # MOT 汇总
    per_frame_results = {}      # 每帧 label

    # ========== Track ID 重映射: 按首次出现顺序从 1 连续编号 ==========
    id_remap = {}               # {原始 track_id: 新连续 id}
    next_remap_id = 1

    for frame_idx, img_file in enumerate(tqdm(image_files, desc="处理图像"), start=1):
        # 输出进度信息（用于 video_processor 解析）
        progress_pct = int((frame_idx - 1) / len(image_files) * 100)
        print(f"PROGRESS: {frame_idx}/{len(image_files)}|{progress_pct}", flush=True)

        # 读取原图
        img = cv2.imread(str(img_file))
        if img is None:
            print(f"无法读取: {img_file}")
            continue

        im0 = img.copy()
        img_h, img_w = im0.shape[:2]

        # YOLO 推理
        results = model.predict(source=str(img_file), conf=conf, imgsz=imgsz, verbose=False)

        if len(results) == 0:
            save_path = output_path / f"{img_file.stem}.png"
            cv2.imwrite(str(save_path), im0)
            frames.append(im0.copy())
            per_frame_results[img_file.stem] = []
            continue

        result = results[0]

        # 检查结果格式
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            det = result[0]
            masks = result[1]
        elif hasattr(result, 'boxes'):
            det = torch.cat([result.boxes.xyxy, result.boxes.conf.unsqueeze(1), result.boxes.cls.unsqueeze(1)], dim=1)
            masks = result.masks.data if result.masks is not None else None
        else:
            save_path = output_path / f"{img_file.stem}.png"
            cv2.imwrite(str(save_path), im0)
            frames.append(im0.copy())
            per_frame_results[img_file.stem] = []
            continue

        if det is None or len(det) == 0:
            save_path = output_path / f"{img_file.stem}.png"
            cv2.imwrite(str(save_path), im0)
            frames.append(im0.copy())
            per_frame_results[img_file.stem] = []
            continue

        # 提取检测信息
        det_boxes = det[:, :4].cpu().numpy()
        det_confs = det[:, 4].cpu().numpy()
        det_cls = det[:, 5].cpu().numpy()

        # 准备 DeepSORT 输入
        xywh_bboxs = []
        confs = []
        oids = []

        for i in range(len(det_boxes)):
            x1, y1, x2, y2 = det_boxes[i]
            cx, cy, w, h = xyxy_to_xywh(x1, y1, x2, y2)
            xywh_bboxs.append([cx, cy, w, h])
            confs.append([det_confs[i]])
            oids.append(int(det_cls[i]))

        xywhs = torch.Tensor(xywh_bboxs)
        confss = torch.Tensor(confs)

        # DeepSORT 更新
        outputs = deepsort.update(xywhs, confss, oids, im0)

        frame_labels = []

        if len(outputs) > 0:
            for output in outputs:
                track_box = output[:4]
                track_id_raw = int(output[-2])
                class_id = int(output[-1])

                # --- ID 重映射 ---
                if track_id_raw not in id_remap:
                    id_remap[track_id_raw] = next_remap_id
                    next_remap_id += 1
                track_id = id_remap[track_id_raw]

                tx1, ty1, tx2, ty2 = track_box
                bb_left = float(tx1)
                bb_top = float(ty1)
                bb_w = float(tx2 - tx1)
                bb_h = float(ty2 - ty1)

                # --- MOT 格式: frame, id, bb_left, bb_top, bb_width, bb_height, conf, class, visibility ---
                all_tracking_results.append([
                    frame_idx, track_id,
                    round(bb_left, 2), round(bb_top, 2),
                    round(bb_w, 2), round(bb_h, 2),
                    1.0, class_id, 1
                ])

                # --- 每帧 label 格式 (归一化坐标): track_id class_id xc yc w h ---
                xc_norm = round((bb_left + bb_w / 2) / img_w, 6)
                yc_norm = round((bb_top + bb_h / 2) / img_h, 6)
                w_norm = round(bb_w / img_w, 6)
                h_norm = round(bb_h / img_h, 6)
                frame_labels.append([track_id, class_id, xc_norm, yc_norm, w_norm, h_norm])

                # 找到对应的掩模
                best_iou = 0
                best_idx = -1
                for di, det_box in enumerate(det_boxes):
                    iou = box_iou(track_box, det_box)
                    if iou > best_iou:
                        best_iou = iou
                        best_idx = di

                if best_idx >= 0 and best_iou > 0.3 and masks is not None:
                    draw_mask_by_trackid(im0, masks[best_idx], track_id, alpha=0.5)

                draw_box_and_label(im0, track_box, track_id)

                center = (int((track_box[0] + track_box[2]) / 2), int((track_box[1] + track_box[3]) / 2))
                draw_trajectory(im0, track_id, center)

        per_frame_results[img_file.stem] = frame_labels

        # 保存 PNG
        save_path = output_path / f"{img_file.stem}.png"
        cv2.imwrite(str(save_path), im0)
        frames.append(im0.copy())

    print(f"\nPNG 图像已保存到: {output_path}")

    # ========== 保存 TXT 追踪结果 ==========

    # 1. MOT 格式汇总文件: frame, id, bb_left, bb_top, bb_width, bb_height, conf, class, visibility
    mot_path = output_path / "tracking_results_mot.txt"
    with open(mot_path, 'w') as f:
        f.write("# MOT format: frame, track_id, bb_left, bb_top, bb_width, bb_height, conf, class, visibility\n")
        for row in all_tracking_results:
            f.write(','.join(map(str, row)) + '\n')
    print(f"MOT 格式追踪结果已保存到: {mot_path}  (共 {len(all_tracking_results)} 条记录)")

    # 2. 每帧单独的 label 文件: track_id class_id x_center y_center width height (归一化坐标)
    labels_dir = output_path / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)
    for frame_name, rows in per_frame_results.items():
        label_file = labels_dir / f"{frame_name}.txt"
        with open(label_file, 'w') as f:
            for row in rows:
                f.write(' '.join(map(str, row)) + '\n')
    print(f"每帧 label 文件已保存到: {labels_dir}/  (共 {len(per_frame_results)} 帧)")

    # 3. 轨迹统计摘要
    if all_tracking_results:
        summary_path = output_path / "tracking_summary.txt"
        track_ids = set(row[1] for row in all_tracking_results)
        with open(summary_path, 'w') as f:
            f.write(f"总帧数: {len(image_files)}\n")
            f.write(f"总检测记录数: {len(all_tracking_results)}\n")
            f.write(f"唯一轨迹数 (unique track IDs): {len(track_ids)}\n")
            f.write(f"Track ID 范围: {min(track_ids)} ~ {max(track_ids)}\n")
            f.write(f"(ID 已重映射为连续编号, 原始 DeepSORT 最大 ID: {max(id_remap.keys()) if id_remap else 0})\n\n")
            f.write("track_id | 出现帧数 | 首次出现帧 | 最后出现帧\n")
            f.write("-" * 50 + "\n")
            for tid in sorted(track_ids):
                tid_rows = [r for r in all_tracking_results if r[1] == tid]
                frames_appeared = [r[0] for r in tid_rows]
                f.write(f"  {tid:5d}  |  {len(tid_rows):5d}   |    {min(frames_appeared):5d}    |    {max(frames_appeared):5d}\n")
        print(f"轨迹统计摘要已保存到: {summary_path}")

    # ========== 生成视频 ==========
    if len(frames) > 1:
        video_path = output_path / "tracking_result.mp4"
        h, w = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(video_path), fourcc, fps, (w, h))
        for frame in frames:
            writer.write(frame)
        writer.release()
        print(f"视频已保存到: {video_path}")

    # 清理轨迹数据
    data_deque.clear()

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="按 track_id 着色掩模的跟踪可视化 + TXT 结果输出")
    parser.add_argument("--model", "-m", type=str,
                        default="runs/segment/HT22_s_1024/weights/best.pt",
                        help="模型路径")
    parser.add_argument("--source", "-s", type=str,
                        default="data/HT22/01",
                        help="输入图像目录")
    parser.add_argument("--output", "-o", type=str,
                        default="outputs/tracking_colored",
                        help="输出目录")
    parser.add_argument("--conf", type=float, default=0.25,
                        help="置信度阈值")
    parser.add_argument("--imgsz", type=int, default=1024,
                        help="图像尺寸")
    parser.add_argument("--fps", type=int, default=10,
                        help="视频帧率")

    args = parser.parse_args()

    run_tracking_with_colored_masks(
        model_path=args.model,
        source_dir=args.source,
        output_dir=args.output,
        conf=args.conf,
        imgsz=args.imgsz,
        fps=args.fps
    )
