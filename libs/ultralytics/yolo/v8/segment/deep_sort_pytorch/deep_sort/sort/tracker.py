# vim: expandtab:ts=4:sw=4
from __future__ import absolute_import
import numpy as np
from . import kalman_filter
from . import linear_assignment
from . import iou_matching
from .track import Track


class Tracker:
    """
    Multi-target tracker with configurable ReID usage.

    Parameters
    ----------
    metric : nn_matching.NearestNeighborDistanceMetric
    max_iou_distance : float
    max_age : int
    n_init : int
    use_reid : bool
        True  = DeepSORT (cascade appearance matching + IoU fallback)
        False = Cascaded IoU-only (prioritized by recency, no appearance features)
    """

    def __init__(self, metric, max_iou_distance=0.7, max_age=70, n_init=3,
                 use_reid=True):
        self.metric = metric
        self.max_iou_distance = max_iou_distance
        self.max_age = max_age
        self.n_init = n_init
        self.use_reid = use_reid

        self.kf = kalman_filter.KalmanFilter()
        self.tracks = []
        self._next_id = 1

    def predict(self):
        """Propagate track state distributions one time step forward."""
        for track in self.tracks:
            track.predict(self.kf)

    def increment_ages(self):
        for track in self.tracks:
            track.increment_age()
            track.mark_missed()

    def update(self, detections):
        """Perform measurement update and track management."""
        # Run matching.
        matches, unmatched_tracks, unmatched_detections = \
            self._match(detections)

        # Update track set.
        for track_idx, detection_idx in matches:
            self.tracks[track_idx].update(
                self.kf, detections[detection_idx])
        for track_idx in unmatched_tracks:
            self.tracks[track_idx].mark_missed()
        for detection_idx in unmatched_detections:
            self._initiate_track(detections[detection_idx])
        self.tracks = [t for t in self.tracks if not t.is_deleted()]

        # Update distance metric.
        active_targets = [t.track_id for t in self.tracks if t.is_confirmed()]
        features, targets = [], []
        for track in self.tracks:
            if not track.is_confirmed():
                continue
            features += track.features
            targets += [track.track_id for _ in track.features]
            track.features = []
        self.metric.partial_fit(
            np.asarray(features), np.asarray(targets), active_targets)

    def _match(self, detections):
        if self.use_reid:
            return self._match_cascade_reid(detections)
        else:
            return self._match_cascade_iou(detections)

    # ================================================================
    #  模式 1: 原版 DeepSORT — 外观级联匹配 + IoU 兜底
    # ================================================================
    def _match_cascade_reid(self, detections):
        def gated_metric(tracks, dets, track_indices, detection_indices):
            features = np.array([dets[i].feature for i in detection_indices])
            targets = np.array([tracks[i].track_id for i in track_indices])
            cost_matrix = self.metric.distance(features, targets)
            cost_matrix = linear_assignment.gate_cost_matrix(
                self.kf, cost_matrix, tracks, dets, track_indices,
                detection_indices)
            return cost_matrix

        confirmed_tracks = [
            i for i, t in enumerate(self.tracks) if t.is_confirmed()]
        unconfirmed_tracks = [
            i for i, t in enumerate(self.tracks) if not t.is_confirmed()]

        # Step 1: Cascade appearance matching for confirmed tracks
        matches_a, unmatched_tracks_a, unmatched_detections = \
            linear_assignment.matching_cascade(
                gated_metric, self.metric.matching_threshold, self.max_age,
                self.tracks, detections, confirmed_tracks)

        # Step 2: IoU fallback for all unmatched + unconfirmed
        iou_track_candidates = unconfirmed_tracks + list(unmatched_tracks_a)
        unmatched_tracks_a = []
        matches_b, unmatched_tracks_b, unmatched_detections = \
            linear_assignment.min_cost_matching(
                iou_matching.iou_cost, self.max_iou_distance, self.tracks,
                detections, iou_track_candidates, unmatched_detections)

        matches = matches_a + matches_b
        unmatched_tracks = list(set(unmatched_tracks_a + unmatched_tracks_b))
        return matches, unmatched_tracks, unmatched_detections

    # ================================================================
    #  模式 2: 级联 IoU 匹配 — 按 time_since_update 优先级匹配
    #  适合细胞追踪: 无外观特征, 纯几何匹配, 但保留优先级机制
    # ================================================================
    def _match_cascade_iou(self, detections):
        """
        Cascaded IoU matching: match tracks in order of recency.
        Stage 1: tracks with time_since_update == 1 (just predicted, most reliable)
        Stage 2: tracks with time_since_update in [2, 3] (recently lost)
        Stage 3: tracks with time_since_update in [4, max_age] (long-lost, low priority)
        Finally: unconfirmed tracks match remaining detections
        """
        confirmed_tracks = [
            i for i, t in enumerate(self.tracks) if t.is_confirmed()]
        unconfirmed_tracks = [
            i for i, t in enumerate(self.tracks) if not t.is_confirmed()]

        # 按 time_since_update 分组: 越小 = 越近期 = 优先级越高
        # Stage 1: 刚刚预测的轨迹 (time_since_update == 1, 即上一帧刚匹配过)
        stage1 = [i for i in confirmed_tracks
                  if self.tracks[i].time_since_update == 1]
        # Stage 2: 短暂丢失 (2~3帧)
        stage2 = [i for i in confirmed_tracks
                  if 2 <= self.tracks[i].time_since_update <= 3]
        # Stage 3: 较长丢失 (4帧以上), 但 Kalman 已漂移, 用更严格的阈值
        stage3 = [i for i in confirmed_tracks
                  if self.tracks[i].time_since_update > 3]

        all_matches = []
        remaining_detections = list(range(len(detections)))

        # ---- Stage 1: 活跃轨迹, 标准 IoU 阈值 ----
        if stage1 and remaining_detections:
            m, _, remaining_detections = \
                linear_assignment.min_cost_matching(
                    iou_matching.iou_cost, self.max_iou_distance,
                    self.tracks, detections, stage1, remaining_detections)
            all_matches += m

        # ---- Stage 2: 短暂丢失, 标准 IoU 阈值 ----
        if stage2 and remaining_detections:
            m, _, remaining_detections = \
                linear_assignment.min_cost_matching(
                    iou_matching.iou_cost, self.max_iou_distance,
                    self.tracks, detections, stage2, remaining_detections)
            all_matches += m

        # ---- Stage 3: 较长丢失, 更严格阈值 (防止漂移匹配) ----
        if stage3 and remaining_detections:
            strict_threshold = min(self.max_iou_distance, 0.7)
            m, _, remaining_detections = \
                linear_assignment.min_cost_matching(
                    iou_matching.iou_cost, strict_threshold,
                    self.tracks, detections, stage3, remaining_detections)
            all_matches += m

        # ---- Stage 4: 未确认轨迹 ----
        if unconfirmed_tracks and remaining_detections:
            m, _, remaining_detections = \
                linear_assignment.min_cost_matching(
                    iou_matching.iou_cost, self.max_iou_distance,
                    self.tracks, detections, unconfirmed_tracks,
                    remaining_detections)
            all_matches += m

        # 计算未匹配的轨迹
        matched_track_indices = set(m[0] for m in all_matches)
        all_track_indices = set(confirmed_tracks + unconfirmed_tracks)
        unmatched_tracks = list(all_track_indices - matched_track_indices)

        return all_matches, unmatched_tracks, remaining_detections

    def _initiate_track(self, detection):
        mean, covariance = self.kf.initiate(detection.to_xyah())
        self.tracks.append(Track(
            mean, covariance, self._next_id, self.n_init, self.max_age,
            detection.oid, detection.feature))
        self._next_id += 1
