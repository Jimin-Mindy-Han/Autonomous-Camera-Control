# YOLO_DeepSORT가 실시간으로 돌아가면서 person class가 detect된 첫번째 프레임을 캡처
# gpt는 캡처된 프레임을 input으로 받아 text query에 맞는지 확인 후 id 출력
# TODO (2026-01-21:...)
import threading
from datetime import time
import argparse, cv2, os, time
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import gpt_detectmaincharacter as gpt
import joystick_control
import numpy as np
import capture_frame as cf
import queue
from multiprocessing import Process, Queue


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

# 비디오 저장 함수
def save_frames(cap, out):
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Cannot read frame")
        out.write(frame)
        # 영상 캡처가 종료된 경우 스레드를 종료합니다.
        if not cap.isOpened():
            break

def main(frame_queue):
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
    parser.add_argument("--video-dir", type=str, default="result_video", help="Recorded result video file")
    parser.add_argument("--video-name", type=str, default="result_bbox.avi", help="Output video filename")
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

    # # source 처리
    # if args.source.isdigit():
    #     cap = cv2.VideoCapture(int(args.source), cv2.CAP_DSHOW)
    # else:
    #     cap = cv2.VideoCapture(args.source)
    #
    # if not cap.isOpened():
    #     raise RuntimeError(f"Cannot open source: {args.source}")

    # 녹화 설정
    os.makedirs(args.video_dir, exist_ok=True)
    bbox_video_path = os.path.join(str(args.video_dir), str(args.video_name))
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter(bbox_video_path, fourcc, 15.0, (1920,1080))

    # 클래스 필터
    if args.classes.strip() == "":
        class_filter = None
    else:
        class_filter = set(int(x.strip()) for x in args.classes.split(","))

    save_first_frame = False
    os.makedirs(args.save_dir, exist_ok=True)
    save_path = os.path.join(args.save_dir, args.save_name)

    # GPT 피사체 판단 planning 초기화
    result = {"target_id": None, "status": "IDLE"} #status에는 "IDLE", "FOUND", "NOT_FOUND", "PENDING", "CHECKING"

    # cam planning 초기화
    main_x1 = 0
    main_y1 = 0
    main_x2 = 0
    main_y2 = 0
    pan_speed = 0
    last_sweep_time = 0.0
    sweep_phase = "LEFT"
    first_sweep = True
    sweep_started = False

    # cam ctrl 초기화
    last_joystick_time = 0.0
    joystick_interval = 1 / 30
    joystick_was_moving = False

    now = time.time()
    frame_count = 0
    fps_counter_start = 0.0
    while True:
        try:
            frame = frame_queue.get_nowait()
        except queue.Empty:
            continue
        if frame is None:
            continue

        # fps 계산
        frame_count += 1
        if time.time() - fps_counter_start >= 1.0:
            print(f"실시간 처리 FPS: {frame_count}")
            frame_count = 0
            fps_counter_start = time.time()

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
        if result["status"]=="FOUND":
            tracks_to_draw = [t for t in tracks if t.is_confirmed() and t.track_id == result["target_id"]]
            main_x1, main_y1, main_x2, main_y2 = map(int, tracks_to_draw[0].to_ltrb())
        else:
            tracks_to_draw = tracks
        # 5) 시각화
        vis = draw_tracks(frame, tracks_to_draw)
        cv2.imshow("YOLO11 + DeepSORT", vis)
        out.write(vis)

        # frame 캡처
        save_first_frame = cf.capture_frame(save_first_frame, tracks_to_draw, save_path, vis)

        # gpt 피사체 판단 planning
        if save_first_frame:
            if result["status"] == "IDLE":
                thread = threading.Thread(target=gpt.gpt_pick_main_character_id, args=(result,))
                thread.start()
                result["status"] = "PENDING"
            else:
                pass

        print("GPT target ID: ", result["target_id"])
        print("GPT status: ", result["status"])

        # 재탐색 planning
        if result["status"] == "NOT_FOUND":
            # 현재 phase의 sweep 시간을 한번만 찍기
            if not sweep_started:
                last_sweep_time = time.time()
                sweep_started = True
            current_time = time.time()
            # sweep duration 결정
            if sweep_phase == "LEFT":
                duration = 5.0 if first_sweep else 10.0
                pan_direction = -1.0
            else:
                duration = 10.0
                pan_direction = 1.0
            # sweep duration 동안 sweep
            if (current_time - last_sweep_time) < duration:
                pan_speed = 0.2 * pan_direction
            else:
                pan_speed = 0.0
                save_first_frame = False
                result["status"] = "IDLE"
                # 다음 phase 전환 및 reset
                if sweep_phase == "LEFT":
                    first_sweep = False
                    sweep_phase = "RIGHT"
                    sweep_started = False
                else:
                    sweep_phase = "LEFT"
                    sweep_started = False

        if result["status"] == "FOUND":
            # 프레임 중앙으로부터 main character의 오차 계산, pan speed planning
            frame_center_x = frame.shape[1] // 2
            frame_center_y = frame.shape[0] // 2
            main_center_x = (main_x1 + main_x2) // 2
            main_center_y = (main_y1 + main_y2) // 2
            dx = main_center_x - frame_center_x; dy = main_center_y - frame_center_y
            if abs(dx) > 5:
                pan_direction = np.sign(dx)
                pan_speed = 0.2 * pan_direction

        # cam control
        current_time = time.time()
        if (current_time - last_joystick_time)>=joystick_interval:
            joystick_control.joystickMoveHeadPLUS("205C32454D31", pan_speed, 0)
            last_joystick_time = current_time
            joystick_was_moving = True
        elif joystick_was_moving:
            joystick_control.joystickMoveHeadPLUS("205C32454D31", 0.0, 0.0)
            joystick_was_moving = False
        
        # 실시간 스트리밍 종료
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord("q"):
            break

    out.release()
    print("총 녹화시간: ", round(now - time.time(), 2))
    cv2.destroyAllWindows()

def raw_video(frame_queue):
    # source 처리
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open source: 0")
    # 녹화 설정
    video_path = "result_video/result.avi"
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter(video_path, fourcc, 60.0, (int(cap.get(3)), int(cap.get(4))))
    now = time.time()
    while True:
        success, frame = cap.read()
        if not success:
            print("Cannot read frame")
            break

        try:
            if frame_queue.full():
                frame_queue.get_nowait()
            frame_queue.put_nowait(frame)
        except (queue.Empty, queue.Full):
            pass
        out.write(frame)
        cv2.imshow("frame", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break
    cap.release()
    out.release()
    print("총 녹화 시간: ", round(time.time() - now, 2))
    cv2.destroyAllWindows()



if __name__ == "__main__":
    frame_queue = Queue(maxsize=1)
    process1 = Process(target=raw_video, args=(frame_queue, ))
    process1.daemon = True
    process2 = Process(target=main, args=(frame_queue,))

    process1.start()
    process2.start()

    process2.join()


