import cv2
import numpy as np
import focusMove
import time

def is_image_in_focus(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gb_gray = cv2.GaussianBlur(gray, (3, 3), 0)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    # gb_laplacian = cv2.Laplacian(gb_gray, cv2.CV_64F)
    focus_measure = laplacian.var()
    return focus_measure, laplacian

cap = cv2.VideoCapture(0)

best_score_saved = False
current_direction = 200
delEnc = 0
prev_score = 0
joystickWasRunning = False
# best_score = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    key = cv2.waitKey(1) & 0xFF

    score, edge_frame = is_image_in_focus(frame)
    score = round(score, 2)
    cv2.putText(frame, f"Sharpness: {score:.2f}", (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # 여기에 focus 조절
    if not best_score_saved:
        best_score_saved = True
        best_score = score
    if score >= best_score:
        best_score = score
        delEnc = 0
    else:
        if score >= prev_score:
            delEnc = current_direction
        else:
            current_direction = - current_direction
            delEnc = current_direction
    print(f"best_score: {best_score}, current_score: {score}, prev_score: {prev_score}")
    prev_score = score

    # while 문 안에서 지속적으로 focus encoder 가 움직이도록 만드는 코드
    if delEnc != 0:
        focusMove.focusManualMove(focusMove.LinkID, delEnc)
        joystickWasRunning = True
    elif joystickWasRunning:
        joystickWasRunning = False
        focusMove.focusManualMove(focusMove.LinkID, 0)


    edge_frame = cv2.convertScaleAbs(edge_frame, alpha=4.0)
    cv2.imshow("Edge Detection", edge_frame)

    # 화면 출력
    cv2.imshow("Frame", frame)
    time.sleep(0.025)


    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
