# Ultralytics YOLO 🚀, GPL-3.0 license

import hydra
import torch
import json
from pathlib import Path

from ultralytics.yolo.utils import DEFAULT_CONFIG, ROOT, ops
from ultralytics.yolo.utils.checks import check_imgsz
from ultralytics.yolo.utils.plotting import colors, save_one_box

from ultralytics.yolo.v8.detect.predict import DetectionPredictor
from numpy import random

import cv2
import sys
import os

# 修复: 确保 deep_sort_pytorch 可从任意CWD导入
_SEGMENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SEGMENT_DIR not in sys.path:
    sys.path.insert(0, _SEGMENT_DIR)

from deep_sort_pytorch.utils.parser import get_config
from deep_sort_pytorch.deep_sort import DeepSort
from collections import deque
import numpy as np

palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)
data_deque = {}
deepsort = None


def init_tracker():
    global deepsort
    cfg_deep = get_config()
    cfg_deep.merge_from_file(os.path.join(_SEGMENT_DIR, "deep_sort_pytorch/configs/deep_sort.yaml"))

    deepsort = DeepSort(
        cfg_deep.DEEPSORT.REID_CKPT,
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


def xyxy_to_xywh(*xyxy):
    """Calculates the relative bounding box from absolute pixel values."""
    bbox_left = min([xyxy[0].item(), xyxy[2].item()])
    bbox_top = min([xyxy[1].item(), xyxy[3].item()])
    bbox_w = abs(xyxy[0].item() - xyxy[2].item())
    bbox_h = abs(xyxy[1].item() - xyxy[3].item())
    x_c = (bbox_left + bbox_w / 2)
    y_c = (bbox_top + bbox_h / 2)
    return x_c, y_c, bbox_w, bbox_h


def compute_color_for_labels(label):
    if label == 0:
        color = (85, 45, 255)
    elif label == 2:
        color = (222, 82, 175)
    elif label == 3:
        color = (0, 204, 255)
    elif label == 5:
        color = (0, 149, 255)
    else:
        color = [int((p * (label ** 2 - label + 1)) % 255) for p in palette]
    return tuple(color)


def UI_box(x, img, color=None, label=None, line_thickness=None):
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        cv2.rectangle(img, (c1[0], c1[1] - t_size[1] - 3), (c1[0] + t_size[0], c1[1] + 3), color, -1, cv2.LINE_AA)
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)


def draw_boxes(img, bbox, names, object_id, identities=None, offset=(0, 0)):
    height, width, _ = img.shape
    for key in list(data_deque):
        if key not in identities:
            data_deque.pop(key)

    for i, box in enumerate(bbox):
        x1, y1, x2, y2 = [int(v) for v in box]
        x1 += offset[0]
        x2 += offset[0]
        y1 += offset[1]
        y2 += offset[1]

        center = (int((x2 + x1) / 2), int((y2 + y1) / 2))
        id = int(identities[i]) if identities is not None else 0

        if id not in data_deque:
            data_deque[id] = deque(maxlen=64)

        color = compute_color_for_labels(object_id[i])
        obj_name = names[object_id[i]]
        label = f"{id}:{obj_name}"

        data_deque[id].appendleft(center)
        UI_box(box, img, label=label, color=color, line_thickness=2)

        for j in range(1, len(data_deque[id])):
            if data_deque[id][j - 1] is None or data_deque[id][j] is None:
                continue
            thickness = int(np.sqrt(64 / float(j + j)) * 1.5)
            cv2.line(img, data_deque[id][j - 1], data_deque[id][j], color, thickness)
    return img


class SegmentationPredictor(DetectionPredictor):

    def postprocess(self, preds, img, orig_img):
        masks = []
        p = ops.non_max_suppression(
            preds[0],
            self.args.conf,
            self.args.iou,
            agnostic=self.args.agnostic_nms,
            max_det=self.args.max_det,
            nm=32
        )
        proto = preds[1][-1]
        for i, pred in enumerate(p):
            shape = orig_img[i].shape if self.webcam else orig_img.shape
            if not len(pred):
                continue
            if self.args.retina_masks:
                pred[:, :4] = ops.scale_boxes(img.shape[2:], pred[:, :4], shape).round()
                masks.append(ops.process_mask_native(proto[i], pred[:, 6:], pred[:, :4], shape[:2]))
            else:
                masks.append(ops.process_mask(proto[i], pred[:, 6:], pred[:, :4], img.shape[2:], upsample=True))
                pred[:, :4] = ops.scale_boxes(img.shape[2:], pred[:, :4], shape).round()
        
        # 清理proto和preds以释放显存
        del proto, preds
        torch.cuda.empty_cache()
        
        return (p, masks)

    def write_results(self, idx, preds, batch):
        p, im, im0 = batch
        log_string = ""
        if len(im.shape) == 3:
            im = im[None]
        self.seen += 1

        if self.webcam:
            log_string += f'{idx}: '
            frame = self.dataset.count
        else:
            frame = getattr(self.dataset, 'frame', 0)

        self.data_path = p
        self.txt_path = str(self.save_dir / 'labels' / p.stem) + ('' if self.dataset.mode == 'image' else f'_{frame}')
        log_string += '%gx%g ' % im.shape[2:]
        self.annotator = self.get_annotator(im0)

        preds, masks = preds
        det = preds[idx]
        if len(det) == 0:
            return log_string

        mask = masks[idx]
        h0, w0 = im0.shape[:2]

        # Segments - 保持与det一致的顺序（不要reversed）
        segments = []
        if self.args.save_txt:
            segments = [
                ops.scale_segments(im0.shape if self.args.retina_masks else im.shape[2:], x, im0.shape, normalize=True)
                for x in ops.masks2segments(mask)
            ]

        # Print results
        for c in det[:, 5].unique():
            n = (det[:, 5] == c).sum()
            log_string += f"{n} {self.model.names[int(c)]}{'s' * (n > 1)}, "

        # Mask plotting - 显存优化
        torch.cuda.empty_cache()
        max_masks = 80
        if len(mask) > max_masks:
            conf_sorted_idx = det[:, 4].argsort(descending=True)[:max_masks]
            mask_plot = mask[conf_sorted_idx]
            det_for_colors = det[conf_sorted_idx]
        else:
            mask_plot = mask
            det_for_colors = det

        self.annotator.masks(
            mask_plot,
            colors=[colors(x, True) for x in det_for_colors[:, 5]],
            im_gpu=torch.as_tensor(im0, dtype=torch.float16).to(self.device).permute(2, 0, 1).flip(0).contiguous() / 255
            if self.args.retina_masks else im[idx]
        )
        torch.cuda.empty_cache()

        # 保存det用于后续处理
        det_orig = det.clone()
        # 只保存det信息，不保存mask（避免GPU内存累积）
        self.all_outputs.append([det_orig.cpu(), None])
        
        # 清理mask的GPU内存
        del mask
        torch.cuda.empty_cache()

        # 构建跟踪输入和注解
        xywh_bboxs = []
        confs = []
        oids = []
        annotations = []

        for j in range(det_orig.shape[0]):
            xyxy = det_orig[j, :4]
            conf = float(det_orig[j, 4].item())
            cls = int(det_orig[j, 5].item())

            x_c, y_c, bbox_w, bbox_h = xyxy_to_xywh(*xyxy)
            xywh_bboxs.append([float(x_c), float(y_c), float(bbox_w), float(bbox_h)])
            confs.append(float(conf))
            oids.append(int(cls))

            x1, y1, x2, y2 = [float(v) for v in xyxy]
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0

            # 获取分割点坐标(像素坐标)
            if j < len(segments):
                seg_norm = segments[j]
                points = [[round(float(pt[0] * w0), 2), round(float(pt[1] * h0), 2)] for pt in seg_norm]
            else:
                points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]

            class_name = self.model.names[cls] if cls < len(self.model.names) else f"class_{cls}"
            annotations.append({
                'label': f"{class_name}{j}",
                'class_id': cls,
                'class_name': class_name,
                'confidence': round(conf, 4),
                'points': points,
                'center': [round(cx, 2), round(cy, 2)],
                'bbox': [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)]
            })

        # DeepSORT跟踪
        global deepsort
        do_track = getattr(self.args, 'track', True)
        track_results = []

        if do_track:
            if deepsort is None:
                init_tracker()

            xywhs_np = np.array(xywh_bboxs)
            confss_np = np.array(confs)
            outputs = deepsort.update(xywhs_np, confss_np, oids, im0)

            # 内存优化: 清理DeepSORT的旧轨迹
            try:
                if hasattr(deepsort, 'tracker') and deepsort.tracker is not None:
                    deepsort.tracker.tracks = [t for t in deepsort.tracker.tracks if t.time_since_update <= 15]
                    if hasattr(deepsort.tracker, 'metric') and hasattr(deepsort.tracker.metric, 'samples'):
                        active_ids = set(t.track_id for t in deepsort.tracker.tracks if t.is_confirmed())
                        deepsort.tracker.metric.samples = {
                            k: v for k, v in deepsort.tracker.metric.samples.items() if k in active_ids
                        }
            except Exception:
                pass

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            if len(outputs) > 0:
                bbox_xyxy = outputs[:, :4]
                identities = outputs[:, -2]
                object_id = outputs[:, -1]
                draw_boxes(im0, bbox_xyxy, self.model.names, object_id, identities)

                # 收集跟踪结果，并关联到annotations
                for i in range(len(outputs)):
                    track_id = int(identities[i])
                    track_bbox = [float(v) for v in bbox_xyxy[i]]
                    track_results.append({
                        'track_id': track_id,
                        'bbox': track_bbox,
                        'class_id': int(object_id[i])
                    })
                    
                    # 尝试将track_id关联到最近的annotation
                    for ann in annotations:
                        ann_bbox = ann['bbox']
                        # 计算IoU或距离来匹配
                        iou = self._calc_iou(ann_bbox, track_bbox)
                        if iou > 0.5 and 'track_id' not in ann:
                            ann['track_id'] = track_id
                            break

        # === 保存TXT和JSON ===
        try:
            labels_dir = Path(self.save_dir) / 'labels'
            labels_dir.mkdir(parents=True, exist_ok=True)

            if self.args.save_txt:
                # TXT: class_id + 归一化坐标
                txt_file = self.txt_path + '.txt'
                with open(txt_file, 'w') as f:
                    for j, ann in enumerate(annotations):
                        cls_id = ann['class_id']
                        if j < len(segments):
                            seg = segments[j]
                            coords = ' '.join([f"{float(pt[0]):.6f} {float(pt[1]):.6f}" for pt in seg])
                            f.write(f"{cls_id} {coords}\n")

                # JSON: 详细注解
                json_file = self.txt_path + '_masks.json'
                output_data = {
                    'frame': frame,
                    'image_path': str(p),
                    'image_size': [w0, h0],
                    'detections': annotations,
                    'tracks': track_results
                }
                with open(json_file, 'w') as jf:
                    json.dump(output_data, jf, indent=2)

        except Exception as e:
            print(f"保存失败: {e}")

        return log_string

    def _calc_iou(self, box1, box2):
        """计算两个bbox的IoU"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - inter
        
        return inter / union if union > 0 else 0


@hydra.main(version_base=None, config_path=str(DEFAULT_CONFIG.parent), config_name=DEFAULT_CONFIG.name)
def predict(cfg):
    init_tracker()
    cfg.model = cfg.model or "yolov8n-seg.pt"
    cfg.imgsz = check_imgsz(cfg.imgsz, min_dim=2)
    cfg.source = cfg.source if cfg.source is not None else ROOT / "assets"

    predictor = SegmentationPredictor(cfg)
    predictor()


if __name__ == "__main__":
    predict()
