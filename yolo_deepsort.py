# YOLO_DeepSORT가 실시간으로 돌아가면서 person class가 detect된 첫번째 프레임을 캡처

import argparse
import cv2
import os
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

def xyxy_to_ltwh(x1, y1, x2, y2):
    left = float(x1)
    top = float(y1)
    w = float(x2 - x1)
    h = float(y2 - y1)
    return [left, top, w, h]


def draw_tracks(frame, tracks):
    for track in tracks:
        if not track.is_confirmed():
            continue

        track_id = track.track_id

        # Kalman 예측 bbox 대신, 이번 프레임에 매칭된 "원본 detection bbox"가 필요하면 orig=True 사용 가능
        ltrb = track.to_ltrb()  # [left, top, right, bottom]
        if ltrb is None:
            continue

        l, t, r, b = map(int, ltrb)
        cv2.rectangle(frame, (l, t), (r, b), (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"ID {track_id}",
            (l, max(0, t - 7)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
    return frame

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="YOLO11 weights path (e.g., yolo11n.pt or custom.pt)")
    parser.add_argument("--source", type=str, default="0", help="0 for webcam, or /path/to/video.mp4")
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold")
    parser.add_argument("--iou", type=float, default=0.5, help="YOLO NMS IoU threshold")
    parser.add_argument("--classes", type=str, default="", help="Comma-separated class IDs to track (e.g., '0' for person). Empty=all")
    parser.add_argument("--max-age", type=int, default=30, help="DeepSORT max_age")
    parser.add_argument("--n-init", type=int, default=3, help="DeepSORT n_init")
    parser.add_argument("--save-dir", type=str, default="captures", help="Directory to save frames to")
    parser.add_argument("--save-name", type=str, default="YOLO_DeepSORT.jpg", help="Output filename")
    args = parser.parse_args()

    # 1) YOLO11 로드
    model = YOLO(args.model)

    # 2) DeepSORT 로드 (기본 embedder 사용)
    tracker = DeepSort(
        max_age=args.max_age,
        n_init=args.n_init,
        nms_max_overlap=1.0,   # 1.0이면 DeepSORT 내부 NMS 사실상 스킵(기본값)
        max_iou_distance=0.7,
    )

    # source 처리
    if args.source.isdigit():
        cap = cv2.VideoCapture(int(args.source))
    else:
        cap = cv2.VideoCapture(args.source)

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open source: {args.source}")

    # 클래스 필터
    if args.classes.strip() == "":
        class_filter = None
    else:
        class_filter = set(int(x.strip()) for x in args.classes.split(","))

    save_first_frame = False
    os.makedirs(args.save_dir, exist_ok=True)
    save_path = os.path.join(args.save_dir, args.save_name)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 3) YOLO11 추론 (프레임 단위)
        results = model.predict(frame, conf=args.conf, iou=args.iou, verbose=False)
        res = results[0]

        detections = []
        person_detected_in_this_frame = False

        if res.boxes is not None and len(res.boxes) > 0:
            # Ultralytics Boxes: xyxy, conf, cls 텐서 제공
            xyxy = res.boxes.xyxy.cpu().numpy()
            confs = res.boxes.conf.cpu().numpy()
            clss = res.boxes.cls.cpu().numpy().astype(int)

            for (x1, y1, x2, y2), conf, cls_id in zip(xyxy, confs, clss):
                if cls_id != 0:
                    continue
                # if class_filter is not None and cls_id not in class_filter:
                #     continue

                if cls_id == 0:
                    person_detected_in_this_frame = True

                ltwh = xyxy_to_ltwh(x1, y1, x2, y2)
                detections.append((ltwh, float(conf), int(cls_id)))

        # 4) DeepSORT 업데이트 (ID 트래킹)
        tracks = tracker.update_tracks(detections, frame=frame)

        # 5) 시각화
        vis = draw_tracks(frame, tracks)
        cv2.imshow("YOLO11 + DeepSORT", vis)

        # frame 저장
        if not save_first_frame:
            confirmed_exists = any(t.is_confirmed() for t in tracks)
            if confirmed_exists:
                ok = cv2.imwrite(save_path, vis)
                if ok:
                    print(f"[YOLO_DeepSORT.jpg saved] ok={ok}, path = {os.path.abspath(save_path)}")
                    save_first_frame = True
            else:
                print(f"[Warning] failed to save image: {save_path}")

        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

