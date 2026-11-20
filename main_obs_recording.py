# TODO 2026-05-11: target_id가 lost된 경우 appearance 기반 re-identification으로 새 track_id에 재연결하기 -> 현재는 DeepSORT track_id가 사라지면 target tracking이 끊길 수 있음

import argparse, cv2, os, time, threading, csv, json, shutil
import numpy as np
from datetime import datetime
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from obswebsocket import obsws, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from camera_control import joystick_control
import gpt_detectmaincharacter as gpt
import capture_frame as cf
import evaluate_result_qa as erq
import describe_scene_qa as dsq
import replan_shot_qa as rsq
import analyze_log as alog

def xyxy_to_ltwh(x1, y1, x2, y2):
    left = float(x1)
    top = float(y1)
    w = float(x2 - x1)
    h = float(y2 - y1)
    return [left, top, w, h]


def draw_tracks(frame, tracks, target_ids=None):
    if target_ids is None:
        target_ids = set()

    for track in tracks:
        if not track.is_confirmed():
            continue

        track_id = track.track_id

        # Kalman 예측 bbox 대신, 이번 프레임에 매칭된 "원본 detection bbox"가 필요하면 orig=True 사용 가능
        ltrb = track.to_ltrb()  # [left, top, right, bottom]
        if ltrb is None:
            continue

        l, t, r, b = map(int, ltrb)

        if track_id in target_ids:
            color = (0, 255, 0) # green: target
        else: color = (0, 0, 255)  # red: non-target
        cv2.rectangle(frame, (l, t), (r, b), color, 2)
        cv2.putText(
            frame,
            f"ID {track_id}",
            (l, max(0, t - 7)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
    return frame


# 캡처 열기
def open_capture(source, width, height, fps):
    try:
        source_int = int(source)
        cap = cv2.VideoCapture(source_int, cv2.CAP_DSHOW)
    except ValueError:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open source: {source}")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)

    return cap


def make_writer(path, fps, frame_size):
    fourcc = cv2.VideoWriter_fourcc(*"DIVX")
    writer = cv2.VideoWriter(path, fourcc, fps, frame_size)
    if not writer.isOpened():
        raise RuntimeError(f"Cannot open VideoWriter: {path}")
    return writer


def main(shot_plan, run_dir, record_duration=12.0):
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="yolo11n.pt")
    parser.add_argument("--source", type=str, default="2", help="OBS Virtual Camera index or video path")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--max-age", type=int, default=30)
    parser.add_argument("--n-init", type=int, default=3)
    parser.add_argument("--save-dir", type=str, default="captures")
    parser.add_argument("--save-name", type=str, default="YOLO_DeepSORT.jpg")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=float, default=25.0)
    parser.add_argument("--obs-host", type=str, default="localhost")
    parser.add_argument("--obs-port", type=int, default=4455)
    parser.add_argument("--obs-password", type=str, default=os.getenv("OBS_PASSWORD", ""))
    args = parser.parse_args()

    model = YOLO(args.model)
    tracker = DeepSort(
        max_age=args.max_age,
        n_init=args.n_init,
        nms_max_overlap=1.0,
        max_iou_distance=0.7,
    )

    # 영상 스트리밍
    cap = open_capture(args.source, args.width, args.height, args.fps)

    # bbox 녹화
    bbox_avi_path = os.path.join(run_dir, "result_bbox.avi")
    frame_size = (args.width, args.height)
    bbox_out = make_writer(bbox_avi_path, args.fps, frame_size)

    # raw 영상 녹화
    ws = obsws(args.obs_host, args.obs_port, args.obs_password)
    ws.connect()
    obs_recording = False
    raw_path = None

    link_id = os.environ["EDELKRONE_LINK_ID"]

    # OBS에서 설정한 고정 녹화 폴더
    OBS_RECORD_DIR = Path(r"C:\Users\user\Videos")
    before_files = set(OBS_RECORD_DIR.glob("*"))

    log_path = os.path.join(run_dir, "trajectory_log.csv")
    log_file = open(log_path, "w", newline="", encoding="utf-8")
    log_writer = csv.DictWriter(
        log_file,
        fieldnames=[
            "frame_id",
            "time_sec",
            "target_status",
            "target_id",
            "bbox_x1",
            "bbox_y1",
            "bbox_x2",
            "bbox_y2",
            "center_error_x",
            "center_error_y",
            "boundary_margin_left",
            "boundary_margin_right",
            "boundary_margin_top",
            "boundary_margin_bottom",
            "main_target_ratio",
            "non_target_ratio",
            "camera_movement_cmd",
            "pan_speed_cmd",
            "tilt_speed_cmd",
            "slide_speed_cmd",
        ],
    )
    log_writer.writeheader()

    os.makedirs(args.save_dir, exist_ok=True)
    save_path = os.path.join(args.save_dir, args.save_name)
    save_first_frame = False

    result = {"target_id": None, "status": "IDLE"}

    main_x1 = main_y1 = main_x2 = main_y2 = 0
    dx = dy = 0
    pan_speed = tilt_speed = slide_speed = 0.0

    last_joystick_time = 0.0
    joystick_interval = 1 / 30

    frame_count = 0
    target_ratio = 0
    boundary_margin_left = boundary_margin_right = 0
    boundary_margin_top = boundary_margin_bottom = 0
    non_targets = {}

    recording_started = False
    recording_start_time = None
    total_start_time = time.time()
    fps_frame_count = 0
    fps_counter_start = time.time()

    try:
        while True:
            success, frame = cap.read()
            if not success:
                print("Cannot read frame")
                break

            # writer 해상도와 frame 해상도가 다르면 저장 실패/깨짐이 생길 수 있어서 맞춤
            if frame.shape[1] != args.width or frame.shape[0] != args.height:
                frame = cv2.resize(frame, frame_size)

            frame_height, frame_width = frame.shape[:2]
            frame_count += 1

            fps_frame_count += 1
            if time.time() - fps_counter_start >= 1.0:
                print(f"실시간 처리 FPS: {fps_frame_count}")
                fps_frame_count = 0
                fps_counter_start = time.time()

            results = model.predict(frame, conf=args.conf, iou=args.iou, verbose=False)
            res = results[0]

            detections = []
            if res.boxes is not None and len(res.boxes) > 0:
                xyxy = res.boxes.xyxy.cpu().numpy()
                confs = res.boxes.conf.cpu().numpy()
                clss = res.boxes.cls.cpu().numpy().astype(int)

                for (x1, y1, x2, y2), conf, cls_id in zip(xyxy, confs, clss):
                    ltwh = xyxy_to_ltwh(x1, y1, x2, y2)
                    detections.append((ltwh, float(conf), int(cls_id)))

            tracks = tracker.update_tracks(detections, frame=frame)
            target_ids_for_draw = set()
            target_status = "not_selected"
            non_targets = {}

            if result["status"] == "FOUND" and result["target_id"] is not None:
                target_ids_for_draw = set(str(result["target_id"]).split())

                for t in tracks:
                    if not t.is_confirmed():
                        continue
                    track_id = str(t.track_id)
                    if track_id in target_ids_for_draw:
                        continue
                    ltrb = t.to_ltrb()
                    if ltrb is None:
                        continue
                    non_x1, non_y1, non_x2, non_y2 = map(int, ltrb)
                    non_target_ratio = max(0, round((non_y2 - non_y1) * (non_x2 - non_x1), 2))
                    non_targets[track_id] = {
                        "track_id": track_id,
                        "non_target_ratio": non_target_ratio,
                    }

                target_tracks = [
                    t for t in tracks
                    if t.is_confirmed() and str(t.track_id) in target_ids_for_draw
                ]
                main_boxes = [tuple(map(int, t.to_ltrb())) for t in target_tracks if t.to_ltrb() is not None]

                if main_boxes:
                    target_status = "tracked"
                    if not recording_started:
                        recording_started = True
                        recording_start_time = time.time()
                        ws.call(requests.StartRecord())
                        obs_recording = True
                        print("[recording] target detected. Start recording.", flush=True)

                    main_x1 = min(box[0] for box in main_boxes)
                    main_y1 = min(box[1] for box in main_boxes)
                    main_x2 = max(box[2] for box in main_boxes)
                    main_y2 = max(box[3] for box in main_boxes)

                    bbox_width = max(0, main_x2 - main_x1)
                    bbox_height = max(0, main_y2 - main_y1)
                    boundary_margin_left = round(main_x1 / frame_width, 2)
                    boundary_margin_right = round((frame_width - main_x2) / frame_width, 2)
                    boundary_margin_top = round(main_y1 / frame_height, 2)
                    boundary_margin_bottom = round((frame_height - main_y2) / frame_height, 2)
                    target_ratio = round(bbox_height * bbox_width, 2)

                    frame_center_x = frame_width // 2
                    frame_center_y = frame_height // 2
                    main_center_x = (main_x1 + main_x2) // 2
                    main_center_y = (main_y1 + main_y2) // 2
                    dx = main_center_x - frame_center_x
                    dy = main_center_y - frame_center_y
                else:
                    target_status = "lost"

            elapsed = 0.0
            if recording_started and recording_start_time is not None:
                elapsed = time.time() - recording_start_time

            log_writer.writerow({
                "frame_id": frame_count,
                "time_sec": round(elapsed, 4),
                "target_status": target_status,
                "target_id": " ".join(sorted(target_ids_for_draw)),
                "bbox_x1": main_x1,
                "bbox_y1": main_y1,
                "bbox_x2": main_x2,
                "bbox_y2": main_y2,
                "center_error_x": dx,
                "center_error_y": dy,
                "boundary_margin_left": boundary_margin_left,
                "boundary_margin_right": boundary_margin_right,
                "boundary_margin_top": boundary_margin_top,
                "boundary_margin_bottom": boundary_margin_bottom,
                "main_target_ratio": target_ratio,
                "non_target_ratio": json.dumps(non_targets, ensure_ascii=False),
                "camera_movement_cmd": shot_plan["camera_movement"],
                "pan_speed_cmd": pan_speed,
                "tilt_speed_cmd": tilt_speed,
                "slide_speed_cmd": slide_speed,
            })

            vis = draw_tracks(frame.copy(), tracks, target_ids_for_draw)
            cv2.imshow("raw frame", frame)
            cv2.imshow("YOLO11 + DeepSORT", vis)

            if recording_started:
                bbox_out.write(vis)

            save_first_frame = cf.capture_frame(save_first_frame, tracks, save_path, vis)

            if save_first_frame:
                if result["status"] == "IDLE":
                    thread = threading.Thread(
                        target=gpt.gpt_pick_main_character_id,
                        args=(result, shot_plan["subject"]),
                        daemon=True,
                    )
                    thread.start()
                    result["status"] = "PENDING"
                elif result["status"] == "NOT_FOUND":
                    if not recording_started:
                        recording_started = True
                        recording_start_time = time.time()
                        ws.call(requests.StartRecord())
                        obs_recording = True
                        print("[recording] target NOT_FOUND. Start recording.", flush=True)
                    save_first_frame = False

            print("GPT target ID:", result["target_id"])
            print("GPT status:", result["status"])

            pan_speed = 0.0
            slide_speed = 0.0
            tilt_speed = 0.0
            if result["status"] == "FOUND":
                if shot_plan["camera_movement"] == "static":
                    pass
                elif shot_plan["camera_movement"] == "truck_left":
                    slide_speed = -0.2
                elif shot_plan["camera_movement"] == "truck_right":
                    slide_speed = 0.2
                elif shot_plan["camera_movement"] == "track":
                    if abs(dx) > 150:
                        direction_x = np.sign(dx)
                        slide_speed = 0.2 * direction_x
                        pan_speed = 0.25 * direction_x

            current_time = time.time()
            if (current_time - last_joystick_time) >= joystick_interval:
                joystick_control.joystickMoveHeadPLUS(link_id, pan_speed, 0)
                joystick_control.joystickMoveSlide(link_id, slide_speed)
                last_joystick_time = current_time

            if recording_started and recording_start_time is not None:
                if time.time() - recording_start_time >= record_duration:
                    print(f"[recording] {record_duration} seconds recorded. Stop.", flush=True)
                    break

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break

    finally:
        # 안전 정지
        try:
            joystick_control.joystickMoveHeadPLUS(link_id, 0, 0)
            joystick_control.joystickMoveSlide(link_id, 0)
        except Exception as e:
            print("joystick stop failed:", e)

        if obs_recording:
            try:
                ws.call(requests.StopRecord())
                obs_recording = False
            except Exception as e:
                print("OBS stop failed:", e)

        try:
            ws.disconnect()
            time.sleep(4)
            after_files = set(OBS_RECORD_DIR.glob("*"))
            new_files = list(after_files - before_files)

            if new_files:
                recorded_file = max(new_files, key=lambda p: p.stat().st_mtime)
                ext = recorded_file.suffix
                raw_path = os.path.join(run_dir, "result"+ext)
                shutil.move(str(recorded_file), raw_path)
                print("Moved to:", raw_path)

        except Exception as e:
            print("OBS disconnect failed:", e)

        cap.release()
        bbox_out.release()
        log_file.close()
        cv2.destroyAllWindows()

    print("총 실행시간:", round(time.time() - total_start_time, 2))

    bbox_mp4_path = os.path.splitext(bbox_avi_path)[0] + ".mp4"
    erq.avi_2_mp4(bbox_avi_path, bbox_mp4_path)

    return raw_path, bbox_mp4_path


def make_run_dir(base_dir="result_video", base_name="result"):
    os.makedirs(base_dir, exist_ok=True)

    run_dir = os.path.join(base_dir, base_name)
    base = run_dir
    i = 1

    while os.path.exists(run_dir):
        run_dir = f"{base}_{i}"
        i += 1

    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def append_result_as_jsonl(
    save_path: str,
    script: str,
    previous_shot_plan: dict,
    scene_description: dict,
    result_evaluation: dict,
    revised_shot_plan: dict,
) -> None:
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "script": script,
        "previous_shot_plan": previous_shot_plan,
        "scene_description": scene_description,
        "result_evaluation": result_evaluation,
        "revised_shot_plan": revised_shot_plan,
    }

    with open(save_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def is_all_criteria_satisfied(result_evaluation):
    """
    result_evaluation 안의 criteria 결과를 보고 종료 여부를 판단하는 함수.
    """

    criteria = [
        "visibility",
        "framing",
        "narrative",
        "camera_movement",
    ]

    result_analysis = result_evaluation.get("vqa_analysis", {})

    for key in criteria:
        result = result_analysis.get(key, {})
        answer = result.get("answer")

        if answer not in ["success", "partial_success"]:
            return False

    return True


def make_attempt_dir(root_dir, attempt_idx):
    attempt_dir = os.path.join(root_dir, str(attempt_idx))
    os.makedirs(attempt_dir, exist_ok=True)
    return attempt_dir


if __name__ == "__main__":
    script_path = "Script/cave/cave_cut3.txt"
    # script_path = "Script/walking.txt"
    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read()

    shot_plan = {
        "subject": "a mannequin",
        "camera_movement": "truck_left",
    }

    max_attempts = 5
    attempt = 0

    root_run_dir = make_run_dir("result_video", "result")
    answer_save_path = os.path.join(root_run_dir, "answer.jsonl")

    attempt_history = []

    while attempt < max_attempts:
        attempt_idx = attempt + 1
        print(f"\n========== ATTEMPT {attempt_idx} / {max_attempts} ==========")
        print("Current shot_plan:", shot_plan)

        run_dir = make_attempt_dir(root_run_dir, attempt_idx)
        
        # raw 영상 촬영
        RAW_RESULT_PATH, BBOX_RESULT_PATH = main(
            shot_plan=shot_plan,
            run_dir=run_dir,
            record_duration=12.0,
        )

        if not os.path.exists(RAW_RESULT_PATH) or os.path.getsize(RAW_RESULT_PATH) == 0:
            print("RAW_RESULT_PATH does not exist or is empty.")
            break

        base64Frames = erq.process_video(RAW_RESULT_PATH, seconds_per_frame=1)
        scene_description = dsq.video_qa(base64Frames)

        base64Frames_bbox = erq.process_video(BBOX_RESULT_PATH, seconds_per_frame=1)
        LOG_PATH = os.path.join(run_dir, "trajectory_log.csv")
        log_evidence = alog.analyze_log_evidence(csv_path=LOG_PATH, video_path=BBOX_RESULT_PATH, shot_planned_target=shot_plan["subject"])
        result_evaluation = erq.video_qa(script, shot_plan, scene_description, log_evidence, base64Frames)
        revised_shot_plan = rsq.generate_revised_shot_plan(script, shot_plan, scene_description, result_evaluation, attempt_history, attempt_idx)

        append_result_as_jsonl(
            save_path=answer_save_path,
            script=script_path,
            previous_shot_plan=shot_plan.copy(),
            scene_description=scene_description,
            result_evaluation=result_evaluation,
            revised_shot_plan=revised_shot_plan,
        )

        attempt_history.append({
            "attempt": attempt_idx,
            "shot_plan": shot_plan.copy(),
            "scene_description": scene_description,
            "result_evaluation": result_evaluation,
            "revised_shot_plan": revised_shot_plan,
        })

        # 종료 조건: 모든 criteria 만족 시 종료
        if is_all_criteria_satisfied(result_evaluation):
            print("All criteria satisfied. Stop loop.")
            break

        # shot_plan 갱신
        if revised_shot_plan.get("subject") is not None:
            shot_plan["subject"] = revised_shot_plan["subject"]

        if revised_shot_plan.get("camera_movement") is not None:
            shot_plan["camera_movement"] = revised_shot_plan["camera_movement"]

        attempt += 1

    print("Feedback loop finished.")
