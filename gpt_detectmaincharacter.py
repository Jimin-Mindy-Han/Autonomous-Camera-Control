# main_character_gpt.py
import argparse, base64, os
import base64
import os
from dotenv import load_dotenv
from openai import OpenAI
import yolo_deepsort
import queue

# OpenAI API Key
load_dotenv() # .env 파일을 로드
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def image_to_data_url(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].lower().replace(".", "")
    if ext not in ("png", "jpg", "jpeg", "webp"):
        raise ValueError("지원 확장자: png/jpg/jpeg/webp")
    mime = "jpeg" if ext == "jpg" else ext
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{mime};base64,{b64}"


def gpt_pick_main_character_id(result, text_query):
    """
    text_query + (ID가 그려진) image를 넣고, main character의 track id만 문자열로 반환
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-4.1",
                        help="gpt model")
    parser.add_argument("--image_path", type=str, default="captures/YOLO_DeepSORT.jpg", help="Directory to save frames to")
    args = parser.parse_args()

    # OpenAI 로드
    client = OpenAI()

    # image input data url로 바꿔 주기
    data_url = image_to_data_url(args.image_path)

    prompt = f"""
You will be given:
1) a text query describing the main character
2) an image frame where bounding boxes are drawn and each tracked object has a visible numeric ID label.

Task:
- Identify which tracked person/object(s) is(are) the best match for the text query.
- Read the numeric track ID label from the image for that main character.
Output rules (VERY IMPORTANT):
- Output ONLY the ID number(s) (digits only). No words, no punctuation, no extra text.
- If there is no matched person/objects with text query, output "None".
- If there are more than one matching, output the ID numbers separated by a single space. For example, if ID 1 and 2 match the text query, then output "1 2" or "2 1".

Text query:
{text_query}
""".strip() # - Output ONLY the ID number(s) and your reasoning.

    resp = client.responses.create(
        model=args.model,
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": data_url},
            ],
        }],
    )

    out = (resp.output_text or "").strip()

    # 숫자만 남기기
    digits = "".join(ch for ch in out if ch.isdigit() or ch==" ")
    digits = " ".join(digits.split())
    if digits == "":
        answer = None
    else:
        answer = digits

    # None 처리
    low = out.lower()
    if low in ["none"]:
        answer = None

    result["target_id"] = answer

    if answer is None:
        result["status"] = "NOT_FOUND"
    if type(answer) == str:
        result["status"] = "FOUND"

if __name__ == "__main__":
    result = {"target_id": None, "status": "IDLE"}
    gpt_pick_main_character_id(result, "woman")
    print(f"{result}")