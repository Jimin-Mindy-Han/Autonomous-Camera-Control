import cv2, base64, os, time, subprocess, json
from openai import OpenAI
from dotenv import load_dotenv

# OpenAI API Key
load_dotenv() # .env 파일을 로드
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def avi_2_mp4(avi_path, mp4_path):

    cmd = [
        "ffmpeg", "-y",
        "-i", avi_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        mp4_path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{r.stderr}")
    return mp4_path

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

    return base64Frames

def video_qa(base64Frames):
    client = OpenAI()

    with open("QAprompt/scene_description_prompt.txt", "r", encoding="utf-8") as f1:
        qa_prompt = f1.read()

    prompt = f"""{qa_prompt}"""

    qa_response = client.responses.create(
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
    out = qa_response.output_text
    answer = json.loads(out)

    return answer

if __name__ == "__main__":
    VIDEO_PATH = "result_video/result_1/1/result.mp4"
    base64Frames = process_video(VIDEO_PATH, seconds_per_frame=1)
    qa_response = video_qa(base64Frames)
    print(f"qa answer: {qa_response}")
    print(type(qa_response))



