# frame 저장
import cv2, os

def capture_frame(save_first_frame, tracks, save_path, vis):
    if not save_first_frame:
        confirmed_exists = any(t.is_confirmed() for t in tracks)
        if confirmed_exists:
            ok = cv2.imwrite(save_path, vis)
            if ok:
                print(f"[YOLO_DeepSORT.jpg saved] ok={ok}, path = {os.path.abspath(save_path)}")
                save_first_frame = True
        else:
            print(f"[Warning] failed to save image: {save_path}")
    return save_first_frame