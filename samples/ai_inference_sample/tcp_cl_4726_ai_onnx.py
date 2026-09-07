#!/usr/bin/env python3
import json
import os
import queue
import socket
import struct
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
import onnxruntime as ort


# Ap4726Decoder の frame header 長
# 先頭 4 byte に payload size が big-endian uint32 で格納される
LENGTH_SIZE = 4

# YOLO 系 ONNX モデルの既定入力サイズ
# 本サンプルでは正方入力 640 を前提とする
DEFAULT_MODEL_INPUT_SIZE = 640

# 検出候補として残す最小 score
DEFAULT_SCORE_THRESH = 0.25

# NMS の IoU 閾値
DEFAULT_NMS_THRESH = 0.45

# OpenCV 表示時のプレビュー幅
# 元画像が大きい場合でも GUI 表示負荷を抑えるため縮小して表示する
DEFAULT_PREVIEW_WIDTH = 960

# socket.create_connection() の接続タイムアウト秒
DEFAULT_CONNECT_TIMEOUT_SEC = 5.0

# worker 側が queue から frame を待つときの最大待機秒数
DEFAULT_QUEUE_GET_TIMEOUT_SEC = 0.5

# main thread の待機周期
DEFAULT_MAIN_LOOP_SLEEP_SEC = 1.0

# 進捗ログの出力間隔
DEFAULT_LOG_EVERY_N_FRAMES = 30


@dataclass
class AppConfig:
    """
    責務:
    - アプリ全体の実行設定を保持する

    引数:
    - host:
      - Ap4726Decoder の接続先 host
    - port:
      - Ap4726Decoder の接続先 port
    - width:
      - 受信 frame の幅
    - height:
      - 受信 frame の高さ
    - save_dir:
      - PPM 保存先ディレクトリ
    - save_first_n:
      - 先頭何 frame 保存するか
    - queue_size:
      - frame queue の最大保持数
    - reconnect_interval_sec:
      - 切断時の再接続待機秒数
    - model_path:
      - ONNX モデルファイルパス

    戻り値:
    - なし
    """
    host: str = "127.0.0.1"
    port: int = 4726
    width: int = 1920
    height: int = 1080
    save_dir: str = "./ppm_out"
    save_first_n: int = 1
    queue_size: int = 2
    reconnect_interval_sec: float = 2.0
    model_path: str = "./models/yolo11n.onnx"


@dataclass
class AiConfig:
    """
    責務:
    - AI 推論および表示に関する設定を保持する

    引数:
    - model_input_size:
      - モデル入力サイズ
    - score_thresh:
      - score 閾値
    - nms_thresh:
      - NMS の IoU 閾値
    - preview_width:
      - GUI 表示用の縮小プレビュー幅

    戻り値:
    - なし
    """
    model_input_size: int = DEFAULT_MODEL_INPUT_SIZE
    score_thresh: float = DEFAULT_SCORE_THRESH
    nms_thresh: float = DEFAULT_NMS_THRESH
    preview_width: int = DEFAULT_PREVIEW_WIDTH


@dataclass
class RuntimeContext:
    """
    責務:
    - 実行中に共有するオブジェクトをまとめる

    引数:
    - frame_queue:
      - 受信 frame を保持する queue
    - stop_event:
      - 停止通知 event
    - receiver_thread:
      - 受信 thread
    - worker_thread:
      - 処理 thread

    戻り値:
    - なし
    """
    frame_queue: queue.Queue["FramePacket"]
    stop_event: threading.Event
    receiver_thread: threading.Thread
    worker_thread: threading.Thread


@dataclass
class FramePacket:
    """
    責務:
    - 受信した 1 frame 分の情報を worker へ渡す

    引数:
    - index:
      - frame 番号
    - payload_size:
      - payload の byte 数
    - payload:
      - packed BGR bytes
    - received_at:
      - 受信時刻

    戻り値:
    - なし
    """
    index: int
    payload_size: int
    payload: bytes
    received_at: float


class SocketClosedError(Exception):
    """
    責務:
    - server 側切断を通常の通信エラーと区別するための専用例外

    引数:
    - なし

    戻り値:
    - なし
    """
    pass


def load_json_config(config_path: str) -> tuple[AppConfig, AiConfig]:
    """
    責務:
    - JSON 設定ファイルを読み込み AppConfig / AiConfig に変換する

    引数:
    - config_path:
      - JSON 設定ファイルパス

    戻り値:
    - app_config:
      - アプリ実行設定
    - ai_config:
      - AI 推論設定
    """
    with open(config_path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    app_data: dict[str, Any] = data.get("app", {})
    ai_data: dict[str, Any] = data.get("ai", {})

    app_config = AppConfig(
        host=app_data.get("host", AppConfig.host),
        port=app_data.get("port", AppConfig.port),
        width=app_data.get("width", AppConfig.width),
        height=app_data.get("height", AppConfig.height),
        save_dir=app_data.get("save_dir", AppConfig.save_dir),
        save_first_n=app_data.get("save_first_n", AppConfig.save_first_n),
        queue_size=app_data.get("queue_size", AppConfig.queue_size),
        reconnect_interval_sec=app_data.get(
            "reconnect_interval_sec",
            AppConfig.reconnect_interval_sec,
        ),
        model_path=app_data.get("model_path", AppConfig.model_path),
    )

    ai_config = AiConfig(
        model_input_size=ai_data.get(
            "model_input_size",
            AiConfig.model_input_size,
        ),
        score_thresh=ai_data.get("score_thresh", AiConfig.score_thresh),
        nms_thresh=ai_data.get("nms_thresh", AiConfig.nms_thresh),
        preview_width=ai_data.get("preview_width", AiConfig.preview_width),
    )

    return app_config, ai_config


def ensure_output_directory(save_dir: str) -> None:
    """
    責務:
    - 出力先ディレクトリを事前に作成する

    引数:
    - save_dir:
      - 出力先ディレクトリパス

    戻り値:
    - なし
    """
    os.makedirs(save_dir, exist_ok=True)


def print_startup_config(
    config_path: str,
    app_config: AppConfig,
    ai_config: AiConfig,
) -> None:
    """
    責務:
    - 起動時の設定内容をまとめて表示する

    引数:
    - config_path:
      - 読み込んだ設定ファイルパス
    - app_config:
      - アプリ実行設定
    - ai_config:
      - AI 推論設定

    戻り値:
    - なし
    """
    print(
        "[main] start "
        f"config_path={config_path} "
        f"host={app_config.host} "
        f"port={app_config.port} "
        f"width={app_config.width} "
        f"height={app_config.height} "
        f"save_dir={app_config.save_dir} "
        f"save_first_n={app_config.save_first_n} "
        f"queue_size={app_config.queue_size} "
        f"reconnect_interval_sec={app_config.reconnect_interval_sec} "
        f"model_path={app_config.model_path} "
        f"model_input_size={ai_config.model_input_size} "
        f"score_thresh={ai_config.score_thresh} "
        f"nms_thresh={ai_config.nms_thresh} "
        f"preview_width={ai_config.preview_width}"
    )


def recv_exact(sock: socket.socket, size: int) -> bytes:
    """
    責務:
    - 指定 byte 数ちょうど受信するまで読み続ける

    引数:
    - sock:
      - 受信対象 socket
    - size:
      - 必要 byte 数

    戻り値:
    - received_bytes:
      - 受信した bytes

    補足:
    - 接続が途中で切れた場合は SocketClosedError を送出する
    """
    chunks: list[bytes] = []
    remaining = size

    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise SocketClosedError("socket closed while receiving")
        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)


def put_latest(queue_obj: queue.Queue[FramePacket], item: FramePacket) -> None:
    """
    責務:
    - queue が満杯なら古い frame を捨て、常に最新 frame を優先して保持する

    引数:
    - queue_obj:
      - frame 格納先 queue
    - item:
      - 追加する frame packet

    戻り値:
    - なし
    """
    try:
        queue_obj.put_nowait(item)
        return
    except queue.Full:
        pass

    try:
        queue_obj.get_nowait()
    except queue.Empty:
        pass

    queue_obj.put_nowait(item)


def payload_to_bgr_frame(payload: bytes, width: int, height: int) -> np.ndarray:
    """
    責務:
    - packed BGR bytes を numpy の HxWx3 BGR frame に変換する

    引数:
    - payload:
      - packed BGR bytes
    - width:
      - frame width
    - height:
      - frame height

    戻り値:
    - frame_bgr:
      - shape=(height, width, 3) の BGR frame
    """
    expected_size = width * height * 3
    if len(payload) != expected_size:
        raise ValueError(
            f"payload size mismatch: expected={expected_size} actual={len(payload)}"
        )

    frame = np.frombuffer(payload, dtype=np.uint8)
    frame = frame.reshape((height, width, 3))
    return frame


def save_ppm_from_bgr(frame_bgr: np.ndarray, output_path: str) -> None:
    """
    責務:
    - BGR frame を PPM(P6) 形式で保存する

    引数:
    - frame_bgr:
      - shape=(H, W, 3), dtype=uint8 の BGR frame
    - output_path:
      - 出力先ファイルパス

    戻り値:
    - なし
    """
    height, width, channels = frame_bgr.shape
    if channels != 3:
        raise ValueError("frame must have 3 channels")

    frame_rgb = frame_bgr[:, :, ::-1]

    with open(output_path, "wb") as f:
        header = f"P6\n{width} {height}\n255\n".encode("ascii")
        f.write(header)
        f.write(frame_rgb.tobytes())


class AiRunner:
    """
    責務:
    - ONNX Runtime の session 管理
    - 前処理
    - 推論
    - 後処理
    - 描画

    引数:
    - model_path:
      - ONNX モデルファイルパス
    - input_size:
      - モデル入力サイズ
    - score_thresh:
      - score 閾値
    - nms_thresh:
      - NMS 閾値

    戻り値:
    - なし

    補足:
    - 本サンプルは YOLO 系 ONNX モデルを前提とした最小構成例
    """
    def __init__(
        self,
        model_path: str,
        input_size: int = DEFAULT_MODEL_INPUT_SIZE,
        score_thresh: float = DEFAULT_SCORE_THRESH,
        nms_thresh: float = DEFAULT_NMS_THRESH,
    ) -> None:
        self.model_path = model_path
        self.input_size = input_size
        self.score_thresh = score_thresh
        self.nms_thresh = nms_thresh

        self.session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
        )

        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [o.name for o in self.session.get_outputs()]

        print(f"[ai] model={model_path}")
        print(f"[ai] input_name={self.input_name}")
        print(f"[ai] output_names={self.output_names}")

    def preprocess(
        self,
        frame_bgr: np.ndarray,
    ) -> tuple[np.ndarray, dict[str, int]]:
        """
        責務:
        - BGR frame を ONNX 推論入力 tensor に変換する

        引数:
        - frame_bgr:
          - shape=(H, W, 3) の BGR frame

        戻り値:
        - x:
          - shape=(1, 3, input_size, input_size) の float32 tensor
        - meta:
          - 後処理で使う元画像サイズ情報
        """
        orig_h, orig_w = frame_bgr.shape[:2]

        # 最小構成サンプルとして単純 resize を採用する
        # 精度優先であれば letterbox への置き換えを検討する
        resized = cv2.resize(frame_bgr, (self.input_size, self.input_size))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        x = rgb.astype(np.float32) / 255.0
        x = np.transpose(x, (2, 0, 1))
        x = np.expand_dims(x, axis=0)

        meta = {
            "orig_w": orig_w,
            "orig_h": orig_h,
            "input_w": self.input_size,
            "input_h": self.input_size,
        }
        return x, meta

    def infer(self, x: np.ndarray) -> list[np.ndarray]:
        """
        責務:
        - ONNX Runtime で推論を実行する

        引数:
        - x:
          - preprocess 済み入力 tensor

        戻り値:
        - outputs:
          - session.run() の戻り値 list
        """
        return self.session.run(self.output_names, {self.input_name: x})

    def _xywh_to_xyxy(
        self,
        x_center: float,
        y_center: float,
        w: float,
        h: float,
    ) -> tuple[float, float, float, float]:
        """
        責務:
        - 中心座標形式 bbox を左上右下形式へ変換する

        引数:
        - x_center:
          - bbox 中心 x
        - y_center:
          - bbox 中心 y
        - w:
          - bbox 幅
        - h:
          - bbox 高さ

        戻り値:
        - x1:
          - 左上 x
        - y1:
          - 左上 y
        - x2:
          - 右下 x
        - y2:
          - 右下 y
        """
        x1 = x_center - w / 2.0
        y1 = y_center - h / 2.0
        x2 = x_center + w / 2.0
        y2 = y_center + h / 2.0
        return x1, y1, x2, y2

    def _get_prediction_rows(self, outputs: list[np.ndarray]) -> np.ndarray:
        """
        責務:
        - ONNX 出力から prediction 行列を取り出し、
          後段で扱いやすい shape=(N, C) に正規化する

        引数:
        - outputs:
          - ONNX 推論出力 list

        戻り値:
        - pred:
          - shape=(N, C) に正規化した prediction 行列
        """
        out0 = outputs[0]

        if out0.ndim != 3 or out0.shape[0] != 1:
            raise ValueError(f"unexpected output shape: {out0.shape}")

        pred = out0[0]

        # 典型的な YOLO 出力は (84, N) のため、必要なら転置して (N, 84) にそろえる
        if pred.shape[0] < pred.shape[1]:
            pred = pred.transpose(1, 0)

        if pred.shape[1] < 6:
            raise ValueError(
                f"unexpected prediction shape after transpose: {pred.shape}"
            )

        return pred

    def _scale_and_clip_box(
        self,
        cx: float,
        cy: float,
        w: float,
        h: float,
        meta: dict[str, int],
    ) -> tuple[int, int, int, int]:
        """
        責務:
        - モデル入力座標系の bbox を元画像座標へ戻し、
          さらに画面内に収まるようにクリップする

        引数:
        - cx:
          - bbox 中心 x
        - cy:
          - bbox 中心 y
        - w:
          - bbox 幅
        - h:
          - bbox 高さ
        - meta:
          - 元画像サイズと入力サイズ情報

        戻り値:
        - x1:
          - 左上 x
        - y1:
          - 左上 y
        - x2:
          - 右下 x
        - y2:
          - 右下 y
        """
        orig_w = meta["orig_w"]
        orig_h = meta["orig_h"]
        input_w = meta["input_w"]
        input_h = meta["input_h"]

        x1, y1, x2, y2 = self._xywh_to_xyxy(cx, cy, w, h)

        x1 = x1 * orig_w / input_w
        x2 = x2 * orig_w / input_w
        y1 = y1 * orig_h / input_h
        y2 = y2 * orig_h / input_h

        x1 = max(0, min(orig_w - 1, int(x1)))
        y1 = max(0, min(orig_h - 1, int(y1)))
        x2 = max(0, min(orig_w - 1, int(x2)))
        y2 = max(0, min(orig_h - 1, int(y2)))

        return x1, y1, x2, y2

    def _collect_detection_candidates(
        self,
        pred: np.ndarray,
        meta: dict[str, int],
    ) -> tuple[list[list[int]], list[float], list[int]]:
        """
        責務:
        - 生の prediction 行列から score 閾値を満たす候補だけを抽出する

        引数:
        - pred:
          - shape=(N, C) の prediction 行列
        - meta:
          - 元画像サイズと入力サイズ情報

        戻り値:
        - boxes:
          - OpenCV NMS 用の [x, y, w, h] list
        - scores:
          - score list
        - class_ids:
          - class id list
        """
        boxes: list[list[int]] = []
        scores: list[float] = []
        class_ids: list[int] = []

        for row in pred:
            cx, cy, w, h = row[0:4]
            class_scores = row[4:]

            class_id = int(np.argmax(class_scores))
            score = float(class_scores[class_id])

            if score < self.score_thresh:
                continue

            x1, y1, x2, y2 = self._scale_and_clip_box(cx, cy, w, h, meta)

            if x2 <= x1 or y2 <= y1:
                continue

            boxes.append([x1, y1, x2 - x1, y2 - y1])
            scores.append(score)
            class_ids.append(class_id)

        return boxes, scores, class_ids

    def _apply_nms(
        self,
        boxes: list[list[int]],
        scores: list[float],
    ) -> list[int]:
        """
        責務:
        - OpenCV NMS を適用し、採用 index を返す

        引数:
        - boxes:
          - OpenCV NMS 用の [x, y, w, h] list
        - scores:
          - score list

        戻り値:
        - kept_indices:
          - NMS 通過後の index list
        """
        if not boxes:
            return []

        indices = cv2.dnn.NMSBoxes(
            boxes,
            scores,
            self.score_thresh,
            self.nms_thresh,
        )

        if len(indices) == 0:
            return []

        return indices.flatten().tolist()

    def _build_detections(
        self,
        boxes: list[list[int]],
        scores: list[float],
        class_ids: list[int],
        kept_indices: list[int],
    ) -> list[dict[str, int | float | str]]:
        """
        責務:
        - NMS 通過後の index から描画用 detection list を構築する

        引数:
        - boxes:
          - OpenCV NMS 用の [x, y, w, h] list
        - scores:
          - score list
        - class_ids:
          - class id list
        - kept_indices:
          - NMS 通過後の index list

        戻り値:
        - detections:
          - 描画用 detection 情報 list
        """
        detections: list[dict[str, int | float | str]] = []

        for idx in kept_indices:
            x, y, w, h = boxes[idx]
            detections.append(
                {
                    "x1": x,
                    "y1": y,
                    "x2": x + w,
                    "y2": y + h,
                    "score": scores[idx],
                    "class_id": class_ids[idx],
                    "class_name": f"class_{class_ids[idx]}",
                }
            )

        return detections

    def postprocess(
        self,
        outputs: list[np.ndarray],
        meta: dict[str, int],
    ) -> list[dict[str, int | float | str]]:
        """
        責務:
        - YOLO 系出力を bbox / score / class に変換し、
          NMS を通して最終 detection list を返す

        引数:
        - outputs:
          - ONNX 推論出力 list
        - meta:
          - 元画像サイズと入力サイズ情報

        戻り値:
        - detections:
          - 描画用 detection 情報 list
        """
        # ONNX 出力を扱いやすい prediction 行列にそろえる
        pred = self._get_prediction_rows(outputs)

        # score 閾値を満たす bbox 候補を集める
        boxes, scores, class_ids = self._collect_detection_candidates(pred, meta)

        # 重複 bbox を NMS で抑制する
        kept_indices = self._apply_nms(boxes, scores)

        # 描画しやすい detection 形式へ変換する
        return self._build_detections(boxes, scores, class_ids, kept_indices)

    def draw(
        self,
        frame_bgr: np.ndarray,
        detections: list[dict[str, int | float | str]],
        frame_index: int,
        elapsed_ms: float,
    ) -> np.ndarray:
        """
        責務:
        - 推論結果と各種情報を frame に描画する

        引数:
        - frame_bgr:
          - 元の BGR frame
        - detections:
          - 描画用 detection 情報 list
        - frame_index:
          - frame 番号
        - elapsed_ms:
          - AI 処理時間[ms]

        戻り値:
        - vis:
          - 描画済み BGR frame
        """
        vis = frame_bgr.copy()
        height, width = vis.shape[:2]

        # 1. bbox と class / score を描画する
        for det in detections:
            x1 = int(det["x1"])
            y1 = int(det["y1"])
            x2 = int(det["x2"])
            y2 = int(det["y2"])
            score = float(det["score"])
            class_name = str(det["class_name"])

            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(
                vis,
                f"{class_name} {score:.2f}",
                (x1, max(30, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

        # 2. 実行中の確認に useful な情報を左上へ重ねる
        cv2.putText(
            vis,
            f"frame={frame_index}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            vis,
            f"size={width}x{height}",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            vis,
            f"ai_time={elapsed_ms:.2f} ms",
            (30, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            vis,
            f"detections={len(detections)}",
            (30, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 200, 0),
            2,
            cv2.LINE_AA,
        )

        return vis

    def run(
        self,
        frame_bgr: np.ndarray,
        frame_index: int,
    ) -> tuple[np.ndarray, float, list[tuple[int, ...]]]:
        """
        責務:
        - 前処理、推論、後処理、描画を一括実行する

        引数:
        - frame_bgr:
          - 入力 BGR frame
        - frame_index:
          - frame 番号

        戻り値:
        - vis:
          - 描画済み BGR frame
        - elapsed_ms:
          - AI 処理時間[ms]
        - output_shapes:
          - デバッグ用の出力 shape list
        """
        t0 = time.perf_counter()

        x, meta = self.preprocess(frame_bgr)
        outputs = self.infer(x)
        detections = self.postprocess(outputs, meta)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        vis = self.draw(frame_bgr, detections, frame_index, elapsed_ms)

        output_shapes = [o.shape for o in outputs]
        return vis, elapsed_ms, output_shapes


def create_preview_image(vis: np.ndarray, preview_width: int) -> np.ndarray:
    """
    責務:
    - GUI 表示用の縮小プレビュー画像を作成する

    引数:
    - vis:
      - 描画済み BGR frame
    - preview_width:
      - 生成する preview 幅

    戻り値:
    - preview:
      - GUI 表示用の縮小画像
    """
    height, width = vis.shape[:2]
    preview_height = int(height * (preview_width / width))
    return cv2.resize(vis, (preview_width, preview_height))


def show_preview(window_name: str, preview: np.ndarray) -> None:
    """
    責務:
    - OpenCV ウィンドウへプレビュー表示する

    引数:
    - window_name:
      - 表示ウィンドウ名
    - preview:
      - GUI 表示用の縮小画像

    戻り値:
    - なし

    補足:
    - Desktop の GUI 環境での実行を前提とする
    """
    cv2.imshow(window_name, preview)
    cv2.waitKey(1)


def run_ai_inference_onnx(
    frame_bgr: np.ndarray,
    frame_index: int,
    ai_runner: AiRunner,
    ai_config: AiConfig,
) -> None:
    """
    責務:
    - 1 frame 分の ONNX 推論を実行し、可視化表示する

    引数:
    - frame_bgr:
      - 入力 BGR frame
    - frame_index:
      - frame 番号
    - ai_runner:
      - ONNX 推論実行オブジェクト
    - ai_config:
      - AI 推論設定

    戻り値:
    - なし
    """
    vis, elapsed_ms, output_shapes = ai_runner.run(frame_bgr, frame_index)

    # 推論結果をそのまま大画面表示するのではなく、軽量な preview を作って表示する
    preview = create_preview_image(vis, ai_config.preview_width)
    show_preview("recv_ai_client_cv", preview)

    if frame_index % DEFAULT_LOG_EVERY_N_FRAMES == 0:
        print(
            "[worker] ai "
            f"frame={frame_index} "
            f"ai_time_ms={elapsed_ms:.2f} "
            f"output_shapes={output_shapes}"
        )


def connect_to_server(host: str, port: int) -> socket.socket:
    """
    責務:
    - Ap4726Decoder の TCP server へ接続する

    引数:
    - host:
      - 接続先 host
    - port:
      - 接続先 port

    戻り値:
    - sock:
      - 接続済み socket
    """
    return socket.create_connection(
        (host, port),
        timeout=DEFAULT_CONNECT_TIMEOUT_SEC,
    )


def receive_frame_packet(sock: socket.socket, frame_index: int) -> FramePacket:
    """
    責務:
    - socket から 1 frame 分を受信し FramePacket として返す

    引数:
    - sock:
      - 受信対象 socket
    - frame_index:
      - この frame に付与する frame 番号

    戻り値:
    - packet:
      - 受信した 1 frame 分の情報
    """
    length_bytes = recv_exact(sock, LENGTH_SIZE)
    payload_size = struct.unpack("!I", length_bytes)[0]
    payload = recv_exact(sock, payload_size)

    return FramePacket(
        index=frame_index,
        payload_size=payload_size,
        payload=payload,
        received_at=time.time(),
    )


def receiver_loop(
    host: str,
    port: int,
    frame_queue: queue.Queue[FramePacket],
    stop_event: threading.Event,
    reconnect_interval_sec: float,
) -> None:
    """
    責務:
    - server へ接続し frame を受信し続ける
    - 切断時は再接続を繰り返す
    - 受信した frame は queue へ投入する

    引数:
    - host:
      - 接続先 host
    - port:
      - 接続先 port
    - frame_queue:
      - FramePacket を渡す queue
    - stop_event:
      - 停止通知 event
    - reconnect_interval_sec:
      - 再接続待機秒数

    戻り値:
    - なし
    """
    frame_count = 0

    while not stop_event.is_set():
        try:
            # 接続フェーズ
            print(f"[receiver] connecting host={host} port={port}")
            with connect_to_server(host, port) as sock:
                sock.settimeout(None)
                print("[receiver] connected")

                # 受信フェーズ
                while not stop_event.is_set():
                    frame_count += 1
                    packet = receive_frame_packet(sock, frame_count)
                    put_latest(frame_queue, packet)

                    if frame_count % DEFAULT_LOG_EVERY_N_FRAMES == 0:
                        print(
                            "[receiver] frame "
                            f"index={frame_count} "
                            f"payload_size={packet.payload_size} "
                            f"queue_size={frame_queue.qsize()}"
                        )

        except SocketClosedError:
            print("[receiver] server disconnected")
        except (ConnectionRefusedError, TimeoutError, OSError) as exc:
            print(f"[receiver] connection error: {exc}")
        except Exception as exc:
            print(f"[receiver] unexpected error: {exc}")

        if stop_event.is_set():
            break

        # stop されていなければ一定時間待って再接続する
        print(f"[receiver] reconnect after {reconnect_interval_sec:.1f}s")
        stop_event.wait(reconnect_interval_sec)

    print("[receiver] stopped")


def validate_packet_size(packet: FramePacket, expected_size: int) -> bool:
    """
    責務:
    - packet の payload_size が想定どおりかを確認する

    引数:
    - packet:
      - 検証対象 frame packet
    - expected_size:
      - 想定 payload size

    戻り値:
    - is_valid:
      - 妥当なら True、そうでなければ False
    """
    if packet.payload_size != expected_size:
        print(
            "[worker] warning "
            f"frame={packet.index} "
            f"unexpected payload size: expected={expected_size} actual={packet.payload_size}"
        )
        return False

    return True


def save_frame_if_needed(
    frame_bgr: np.ndarray,
    packet: FramePacket,
    save_dir: str,
    save_first_n: int,
    saved_count: int,
) -> int:
    """
    責務:
    - 必要なら先頭 N frame のみ PPM 保存する

    引数:
    - frame_bgr:
      - 保存対象 BGR frame
    - packet:
      - frame 情報
    - save_dir:
      - 保存先ディレクトリ
    - save_first_n:
      - 先頭何 frame 保存するか
    - saved_count:
      - 現在までの保存枚数

    戻り値:
    - updated_saved_count:
      - 更新後の保存枚数
    """
    if saved_count >= save_first_n:
        return saved_count

    output_path = os.path.join(save_dir, f"frame_{packet.index:06d}.ppm")
    save_ppm_from_bgr(frame_bgr, output_path)
    print(f"[worker] saved path={output_path}")
    return saved_count + 1


def process_frame_packet(
    packet: FramePacket,
    app_config: AppConfig,
    ai_runner: AiRunner,
    ai_config: AiConfig,
    saved_count: int,
) -> int:
    """
    責務:
    - 1 frame 分の packet を検証し、
      frame 化、必要なら保存、AI 推論・表示まで実行する

    引数:
    - packet:
      - 処理対象 frame packet
    - app_config:
      - アプリ実行設定
    - ai_runner:
      - ONNX 推論実行オブジェクト
    - ai_config:
      - AI 推論設定
    - saved_count:
      - 現在までの保存枚数

    戻り値:
    - updated_saved_count:
      - 更新後の保存枚数
    """
    expected_size = app_config.width * app_config.height * 3

    # payload size が想定どおりか確認する
    if not validate_packet_size(packet, expected_size):
        return saved_count

    # raw payload を numpy の BGR frame に復元する
    frame_bgr = payload_to_bgr_frame(
        packet.payload,
        app_config.width,
        app_config.height,
    )

    # 必要なら先頭数 frame を保存する
    saved_count = save_frame_if_needed(
        frame_bgr,
        packet,
        app_config.save_dir,
        app_config.save_first_n,
        saved_count,
    )

    # AI 推論と可視化表示を行う
    run_ai_inference_onnx(frame_bgr, packet.index, ai_runner, ai_config)

    return saved_count


def worker_loop(
    frame_queue: queue.Queue[FramePacket],
    stop_event: threading.Event,
    app_config: AppConfig,
    ai_runner: AiRunner,
    ai_config: AiConfig,
) -> None:
    """
    責務:
    - queue から frame を取り出して処理し続ける

    引数:
    - frame_queue:
      - FramePacket を受け取る queue
    - stop_event:
      - 停止通知 event
    - app_config:
      - アプリ実行設定
    - ai_runner:
      - ONNX 推論実行オブジェクト
    - ai_config:
      - AI 推論設定

    戻り値:
    - なし
    """
    saved_count = 0

    while not stop_event.is_set():
        try:
            packet = frame_queue.get(timeout=DEFAULT_QUEUE_GET_TIMEOUT_SEC)
        except queue.Empty:
            continue

        try:
            saved_count = process_frame_packet(
                packet,
                app_config,
                ai_runner,
                ai_config,
                saved_count,
            )
        except Exception as exc:
            print(f"[worker] error frame={packet.index}: {exc}")

    print("[worker] stopped")


def create_ai_runner(app_config: AppConfig, ai_config: AiConfig) -> AiRunner:
    """
    責務:
    - 設定に基づいて AiRunner を生成する

    引数:
    - app_config:
      - アプリ実行設定
    - ai_config:
      - AI 推論設定

    戻り値:
    - ai_runner:
      - 生成した ONNX 推論実行オブジェクト
    """
    return AiRunner(
        model_path=app_config.model_path,
        input_size=ai_config.model_input_size,
        score_thresh=ai_config.score_thresh,
        nms_thresh=ai_config.nms_thresh,
    )


def create_runtime_context(
    app_config: AppConfig,
    ai_runner: AiRunner,
    ai_config: AiConfig,
) -> RuntimeContext:
    """
    責務:
    - queue / event / threads をまとめて生成する

    引数:
    - app_config:
      - アプリ実行設定
    - ai_runner:
      - ONNX 推論実行オブジェクト
    - ai_config:
      - AI 推論設定

    戻り値:
    - context:
      - 実行時共有オブジェクト一式
    """
    frame_queue: queue.Queue[FramePacket] = queue.Queue(maxsize=app_config.queue_size)
    stop_event = threading.Event()

    receiver_thread = threading.Thread(
        target=receiver_loop,
        args=(
            app_config.host,
            app_config.port,
            frame_queue,
            stop_event,
            app_config.reconnect_interval_sec,
        ),
        name="receiver_thread",
        daemon=True,
    )

    worker_thread = threading.Thread(
        target=worker_loop,
        args=(frame_queue, stop_event, app_config, ai_runner, ai_config),
        name="worker_thread",
        daemon=True,
    )

    return RuntimeContext(
        frame_queue=frame_queue,
        stop_event=stop_event,
        receiver_thread=receiver_thread,
        worker_thread=worker_thread,
    )


def start_runtime(context: RuntimeContext) -> None:
    """
    責務:
    - receiver / worker thread を起動する

    引数:
    - context:
      - 実行時共有オブジェクト一式

    戻り値:
    - なし
    """
    context.receiver_thread.start()
    context.worker_thread.start()


def wait_until_interrupted() -> None:
    """
    責務:
    - Ctrl+C が来るまで main thread を待機させる

    引数:
    - なし

    戻り値:
    - なし
    """
    while True:
        time.sleep(DEFAULT_MAIN_LOOP_SLEEP_SEC)


def shutdown_runtime(context: RuntimeContext) -> None:
    """
    責務:
    - 停止通知を出し、thread 終了を待ち、GUI リソースを解放する

    引数:
    - context:
      - 実行時共有オブジェクト一式

    戻り値:
    - なし
    """
    context.stop_event.set()
    context.receiver_thread.join()
    context.worker_thread.join()
    cv2.destroyAllWindows()


def main() -> int:
    """
    責務:
    - 設定を読み込む
    - 実行準備を行う
    - thread 群を起動する
    - 停止要求まで待つ
    - 後始末して終了する

    引数:
    - argv[1]:
      - JSON 設定ファイルパス

    戻り値:
    - exit_code:
      - 正常終了時は 0
    """
    # 設定を読む
    config_path = sys.argv[1] if len(sys.argv) > 1 else "./config.json"
    app_config, ai_config = load_json_config(config_path)

    # 実行前準備をする
    ensure_output_directory(app_config.save_dir)
    print_startup_config(config_path, app_config, ai_config)

    # AI runner と実行コンテキストを作る
    ai_runner = create_ai_runner(app_config, ai_config)
    context = create_runtime_context(app_config, ai_runner, ai_config)

    # worker / receiver を起動する
    start_runtime(context)

    # Ctrl+C まで待機し、最後に確実に後始末する
    try:
        wait_until_interrupted()
    except KeyboardInterrupt:
        print("\n[main] interrupted")
    finally:
        shutdown_runtime(context)

    print("[main] finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
