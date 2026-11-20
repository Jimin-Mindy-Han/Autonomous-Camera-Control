import json, os
from openai import OpenAI
from dotenv import load_dotenv
import describe_scene_qa as dsq
import evaluate_result_qa as erq


# OpenAI API Key
load_dotenv() # .env 파일을 로드
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def generate_revised_shot_plan(
    script: str,
    shot_plan: dict,
    scene_description: dict,
    result_evaluation: dict,
    attempt_history: list,
    current_attempt_index: int,
    model: str = "gpt-4.1",
) -> dict:

    if attempt_history is None:
        attempt_history = []

    attempt_history_text = json.dumps(attempt_history, ensure_ascii=False, indent=2)

    with open("QAprompt/shot_replanning_prompt.txt.disabled", "r", encoding="utf-8") as f1:
        prompt = f1.read()

    input_data = {
        "script": script,
        "prev_shot_plan": shot_plan,
        "scene_description": scene_description,
        "result_evaluation": result_evaluation,
        "attempt_history": attempt_history_text,
        "current_attempt_index": current_attempt_index,
        "maximum_attempts": 5,
    }

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": json.dumps(input_data, ensure_ascii=False, indent=2),
            },
        ],
        temperature=0,
        text={
            "format": {
                "type": "json_object"
            }
        },
    )
    out = response.output_text
    answer = json.loads(out)

    return answer

if __name__ == "__main__":
    script_path = "Script/cave/cave_cut3.txt"
    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read()
    shot_plan = {"subject": "a woman", "camera_movement": "static"}
    VIDEO_PATH = "result_video/result_1/1/result.mp4"
    base64Frames = erq.process_video(VIDEO_PATH, seconds_per_frame=1)
    scene_description = dsq.video_qa(base64Frames)
    result_evaluation = erq.video_qa(script, shot_plan, scene_description, log_evidence, base64Frames)
    qa_response = generate_revised_shot_plan(script, shot_plan, scene_description, result_evaluation)
    print(f"qa answer: {qa_response}")
    print(type(qa_response))