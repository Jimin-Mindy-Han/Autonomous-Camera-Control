import pandas as pd
import ast
from typing import Optional, Union, List, Any, Dict
from openai import OpenAI
import cv2, os, base64, json
from dotenv import load_dotenv

#OpenAI API Key
load_dotenv() # .env 파일을 로드
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def process_video(video_path, seconds_per_frame=2):
    base64Frames = []
    base_video_path, _ = os.path.splitext(video_path)
    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    print("total_frames: ", total_frames)
    fps = video.get(cv2.CAP_PROP_FPS)
    frames_to_skip = int(fps * seconds_per_frame)
    curr_frame = 0

    # 영상 루프 돌면서 프레임 추출
    while curr_frame < total_frames - 1:
        video.set(cv2.CAP_PROP_POS_FRAMES, curr_frame)
        success, frame = video.read()
        if not success:
            print("Cannot read the video")
            break
        _, buffer = cv2.imencode('.jpg', frame)
        base64Frames.append(base64.b64encode(buffer).decode('utf-8'))
        curr_frame += frames_to_skip
    video.release()

    print(f"frames saved: {len(base64Frames)} frames")
    return base64Frames

# planned target과 tracked target이 맞는지 확인
def verify_target_identity_with_vlm(
    shot_planned_target: str,
    base64Frames,
) -> Dict[str, Any]:
    """
    초록색 박스로 표시된 target이 shot plan target과 일치하는지 VLM으로 확인한다.

    Args:
        base64Frames:
            초록색 박스로 target ID가 표시된 frame 이미지
        script_target:
            각본에서 추적해야 하는 target 설명.
            예: "the woman bending down", "a man in a black jacket"

    Returns:
        {
            "identity_match": bool,
            "confidence": str,
            "reason": str
        }
    """
    client = OpenAI()

    prompt = f"""
You are verifying whether the tracked target matches the shot planned target.

The image contains a tracked target highlighted with a green bounding box.
Your task is to judge ONLY the subject inside the green bounding box.

Script target:
"{shot_planned_target}"

Question:
Does the subject inside the green bounding box match the planned target?

Answer in the following JSON format only:
{{
  "identity_match": true or false,
  "confidence": "high" or "medium" or "low",
  "reason": "brief explanation based on visible evidence"
}}

Rules:
- Focus only on the subject inside the green bounding box.
- Do not judge other people or objects unless they help compare identity.
- If the target is not visible enough, set identity_match to false and confidence to "low".
- Do not infer details that are not visible.
"""

    response = client.responses.create(
        model="gpt-4.1",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                *[
                    {"type": "input_image",
                     "image_url": f"data:image/jpg;base64,{x}", } for x in base64Frames
                ],
            ],
        }],
        temperature=0
    )

    out = response.output_text
    answer = json.loads(out)

    return answer

# non target의 area 중 가장 큰 값 추출
def parse_non_target_ratio(
        value,
        default_ratio: float=1.0
) -> Optional[float]:
    """
    non_target_area 컬럼이
    '[{"track_id": "2", "non_target_ratio": 0.46}]'
    형태일 때 ratio 값을 추출한다.

    여러 non-target이 있으면 가장 큰 ratio를 사용한다.

    non-target이 없으면 default ratio=1.0을 반환한다.
    """
    if pd.isna(value):
        return default_ratio

    try:
        parsed = ast.literal_eval(str(value))
    except Exception:
        return default_ratio

    if not isinstance(parsed, list) or len(parsed) == 0:
        return default_ratio

    ratios = []

    for item in parsed:
        if isinstance(item, dict) and "non_target_ratio" in item:
            ratio = item["non_target_ratio"]
            if ratio is not None:
                ratios.append(float(ratio))

    if not ratios:
        return default_ratio

    # narrative dominance에서는 가장 크게 보이는 non-target과 비교하는 것이 적절함
    return max(ratios)

# 주요 피사체와 비주요 피사체의 ratio 비교 => Narrative에 붙일 것
def main_target_dominance(
    csv_path: str,
    main_ratio_col: str = "main_target_ratio",
    non_target_ratio_col: str = "non_target_ratio",
    status_col: str = "target_status",
) -> Optional[float]:
    """
    target_status가 tracked인 프레임에서만
    main_target_ratio / non_target_ratio의 평균을 반환한다.
    """
    df = pd.read_csv(csv_path)

    # tracked인 프레임만 사용
    df = df[df[status_col] == "tracked"]

    if df.empty:
        return None

    main_ratio = pd.to_numeric(df[main_ratio_col], errors="coerce")
    non_target_ratio = df[non_target_ratio_col].apply(parse_non_target_ratio)

    valid_mask = (
        main_ratio.notna()
        & non_target_ratio.notna()
        & (non_target_ratio > 0)
    )

    if valid_mask.sum() == 0:
        return None

    dominance_ratio = main_ratio[valid_mask] / non_target_ratio[valid_mask]

    return float(round(dominance_ratio.mean(), 2))

# target이 프레임에서 이동하는 방향 확인하기
def analyze_target_direction(
    csv_path: str,
    status_col: str = "target_status",
    tracked_value: str = "tracked",
    bbox_x1_col: str = "bbox_x1",
    bbox_x2_col: str = "bbox_x2",
    frame_col: str = "frame_id",
    min_delta: float = 30.0,
)-> Optional[Dict[str, Any]]:
    """
    target bbox 중심 x 좌표의 변화를 통해(첫 프레임과 마지막 프레임에서의 bbox의 중심 x값 비교)
    target이 frame 안에서 왼쪽/오른쪽 중 어디로 이동했는지 판단한다.

    center_x = (bbox_x1 + bbox_x2) / 2
    delta_x > 0  : 오른쪽 이동
    delta_x < 0  : 왼쪽 이동
    """
    df = pd.read_csv(csv_path)

    tracked_indices = df.index[df[status_col] == tracked_value].tolist()

    if not tracked_indices:
        return None

    start_idx = tracked_indices[0]
    after_tracked = df.loc[start_idx:].copy()

    # bbox 좌표 숫자 변환
    after_tracked[bbox_x1_col] = pd.to_numeric(
        after_tracked[bbox_x1_col], errors="coerce"
    )
    after_tracked[bbox_x2_col] = pd.to_numeric(
        after_tracked[bbox_x2_col], errors="coerce"
    )

    # bbox 없는 frame 제거
    after_tracked = after_tracked.dropna(
        subset=[bbox_x1_col, bbox_x2_col]
    )

    if len(after_tracked) < 2:
        return None

    # bbox 중심 x 좌표 계산
    after_tracked["target_center_x"] = (
                                               after_tracked[bbox_x1_col] + after_tracked[bbox_x2_col]
                                       ) / 2

    first_frame = int(after_tracked[frame_col].iloc[0])
    last_frame = int(after_tracked[frame_col].iloc[-1])

    first_x = float(after_tracked["target_center_x"].iloc[0])
    last_x = float(after_tracked["target_center_x"].iloc[-1])

    delta_x = last_x - first_x

    if delta_x > min_delta:
        direction = "right"
    elif delta_x < -min_delta:
        direction = "left"
    else:
        direction = "stable"

    return {
        "tracked_start_frame": first_frame,
        "tracked_end_frame": last_frame,
        "first_center_x": round(first_x, 2),
        "last_center_x": round(last_x, 2),
        "delta_x": round(delta_x, 2),
        "direction": direction,
        "interpretation": (
            "The target moved to the right side of the frame."
            if direction == "right"
            else "The target moved to the left side of the frame."
            if direction == "left"
            else "The target stayed roughly in the same horizontal position."
        ),
    }

# target이 frame 내 안정적인 위치에 있는가
def analyze_target_framing_stability(
        csv_path: str,
        status_col: str = "target_status",
        tracked_value: str = "tracked",
        bbox_x1_col: str = "bbox_x1",
        bbox_x2_col: str = "bbox_x2",
        frame_col: str = "frame_id",
        left_safe_margin = 240.0,
        right_safe_margin = 1680.0,
        stable_ratio_threshold: float = 0.8,
)-> Optional[Dict[str, Any]]:
    """
    tracked 이후 target bbox가 frame 내 안전 영역에 안정적으로 위치하는지 판단한다.

    안정 조건:
        left_safe_margin < bbox_x1 < bbox_x2 < right_safe_margin

    즉, target bbox가 너무 왼쪽/오른쪽 경계에 붙지 않고
    frame 내부에 안정적으로 들어와 있는지를 확인한다.
    """
    df = pd.read_csv(csv_path)

    # tracked 이후만 사용
    tracked_indices = df.index[df[status_col] == tracked_value].tolist()

    if not tracked_indices:
        return None

    start_idx = tracked_indices[0]
    after_tracked = df.loc[start_idx:].copy()

    # bbox 좌표 숫자 변환
    after_tracked[bbox_x1_col] = pd.to_numeric(
        after_tracked[bbox_x1_col], errors="coerce"
    )
    after_tracked[bbox_x2_col] = pd.to_numeric(
        after_tracked[bbox_x2_col], errors="coerce"
    )

    # bbox가 없는 frame 제거
    after_tracked = after_tracked.dropna(
        subset=[bbox_x1_col, bbox_x2_col]
    )

    if len(after_tracked) == 0:
        return None

    # 안정적인 frame 조건
    stable_mask = (
            (after_tracked[bbox_x1_col] > left_safe_margin)
            & (after_tracked[bbox_x1_col] < after_tracked[bbox_x2_col])
            & (after_tracked[bbox_x2_col] < right_safe_margin)
    )

    stable_frame_count = int(stable_mask.sum())
    total_frame_count = int(len(after_tracked))
    unstable_frame_count = total_frame_count - stable_frame_count

    stable_ratio = (
        stable_frame_count / total_frame_count
        if total_frame_count > 0
        else 0.0
    )

    is_stable = stable_ratio >= stable_ratio_threshold

    return {
        "tracked_start_frame": int(after_tracked[frame_col].iloc[0]),
        "tracked_end_frame": int(after_tracked[frame_col].iloc[-1]),
        "safe_region": {
            "left_safe_margin": left_safe_margin,
            "right_safe_margin": right_safe_margin,
            "condition": (
                f"{left_safe_margin} < {bbox_x1_col} "
                f"< {bbox_x2_col} < {right_safe_margin}"
            ),
        },
        "total_frame_count": total_frame_count,
        "stable_frame_count": stable_frame_count,
        "unstable_frame_count": unstable_frame_count,
        "stable_ratio": round(stable_ratio, 3),
        "stable_ratio_threshold": stable_ratio_threshold,
        "is_stable": is_stable,
        "interpretation": (
            "The target stayed in a stable frame region for most of the video."
            if is_stable
            else "The target frequently moved close to the frame boundary or outside the stable region."
        ),
    }

def analyze_log_evidence(
    csv_path: str,
    video_path: Optional[str] = None,
    shot_planned_target: Optional[str] = None,
    seconds_per_frame: int = 2,

    dominance_threshold: float = 1.0,

    direction_min_delta: float = 100.0,

    left_safe_margin: float = 240.0,
    right_safe_margin: float = 1680.0,
    stable_ratio_threshold: float = 0.8,
) -> Dict[str, Any]:
    """
    Trajectory log와 sampled video frames를 기반으로
    rough evidence를 생성한다.

    Evidence categories:
    1. visibility:
       - shot planned target과 sampled frame의 tracked target이 일치하는지 확인

    2. narrative:
       - target / non-target ratio를 통해 target이 두드러지는지 확인

    3. framing:
       - target bbox가 frame 내 safe region에 안정적으로 위치하는지 확인

    4. camera_movement:
       - target bbox 중심 x좌표의 start-to-end displacement로 이동 방향 확인
    """

    evidence = {}

    # --------------------------------------------------
    # 1. Visibility
    # planned target과 sampled frame target이 일치하는지 확인
    # --------------------------------------------------
    if (
        video_path is not None
        and shot_planned_target is not None
    ):
        base64_frames = process_video(
            video_path=video_path,
            seconds_per_frame=seconds_per_frame,
        )

        identity_result = verify_target_identity_with_vlm(
            shot_planned_target=shot_planned_target,
            base64Frames=base64_frames,
        )

        evidence["visibility"] = {
            "function": "verify_target_identity_with_vlm",
            "shot_planned_target": shot_planned_target,
            "result": {
                "identity_match": identity_result.get("identity_match"),
                "confidence": identity_result.get("confidence"),
                "reason": identity_result.get("reason"),
            },
            "evidence_summary": (
                f"Shot planned target: {shot_planned_target}. "
                f"Tracked target identity match: "
                f"{identity_result.get('identity_match')}. "
                f"Confidence: {identity_result.get('confidence')}. "
                f"Reason: {identity_result.get('reason')}"
            ),
        }

    else:
        evidence["visibility"] = {
            "function": "verify_target_identity_with_vlm",
            "shot_planned_target": shot_planned_target,
            "result": None,
            "evidence_summary": (
                "Target identity verification was not executed because "
                "video_path, frame_save_dir, or shot_planned_target was missing."
            ),
        }

    # --------------------------------------------------
    # 2. Narrative
    # target / non-target ratio 확인
    # --------------------------------------------------
    dominance_ratio = main_target_dominance(
        csv_path=csv_path,
    )

    if dominance_ratio is None:
        is_target_dominant = None
        narrative_summary = (
            "Target dominance ratio could not be computed."
        )
    else:
        is_target_dominant = dominance_ratio > dominance_threshold
        narrative_summary = (
            f"Average target/non-target dominance ratio: {dominance_ratio}. "
            f"Dominance threshold: {dominance_threshold}. "
            f"Target visually dominant: {is_target_dominant}."
        )

    evidence["narrative"] = {
        "function": "main_target_dominance",
        "result": {
            "average_target_non_target_ratio": dominance_ratio,
            "dominance_threshold": dominance_threshold,
            "is_target_dominant": is_target_dominant,
        },
        "evidence_summary": narrative_summary,
    }

    # --------------------------------------------------
    # 3. Framing
    # target이 frame 내 안정적인 위치에 있는지 확인
    # --------------------------------------------------
    framing_result = analyze_target_framing_stability(
        csv_path=csv_path,
        left_safe_margin=left_safe_margin,
        right_safe_margin=right_safe_margin,
        stable_ratio_threshold=stable_ratio_threshold,
    )

    if framing_result is None:
        framing_summary = (
            "Target framing stability could not be computed."
        )
    else:
        framing_summary = (
            f"Stable framing frames: "
            f"{framing_result['stable_frame_count']} / "
            f"{framing_result['total_frame_count']} "
            f"(stable_ratio={framing_result['stable_ratio']}). "
            f"Stable threshold: {framing_result['stable_ratio_threshold']}. "
            f"Framing stable: {framing_result['is_stable']}."
        )

    evidence["framing"] = {
        "function": "analyze_target_framing_stability",
        "result": framing_result,
        "evidence_summary": framing_summary,
    }

    # --------------------------------------------------
    # 4. Camera movement
    # target의 frame 내 이동 방향 확인
    # --------------------------------------------------
    direction_result = analyze_target_direction(
        csv_path=csv_path,
        min_delta=direction_min_delta,
    )

    if direction_result is None:
        direction_summary = (
            "Target movement direction could not be computed."
        )
    else:
        direction_summary = (
            f"Target moved {direction_result['direction']} in the frame. "
            f"Center x shifted from "
            f"{direction_result['first_center_x']} to "
            f"{direction_result['last_center_x']} "
            f"(delta_x={direction_result['delta_x']})."
        )

    evidence["camera_movement"] = {
        "function": "analyze_target_direction",
        "result": direction_result,
        "evidence_summary": direction_summary,
    }

    return evidence
if __name__ == "__main__":
    result = analyze_log_evidence(
        csv_path="result_video/result_13/3/trajectory_log.csv",
        video_path="result_video/result_13/3/result_bbox.mp4",
        shot_planned_target="a woman",
        seconds_per_frame=2,

        dominance_threshold=1.0,
        direction_min_delta=100.0,
        left_safe_margin=240.0,
        right_safe_margin=1680.0,
        stable_ratio_threshold=0.8,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))