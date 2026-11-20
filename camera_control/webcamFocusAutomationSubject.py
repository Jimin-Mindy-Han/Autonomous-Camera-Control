import cv2
import numpy as np
import focusMove
import time

# Sharpness 측정 함수
def is_roi_in_focus(frame, bbox):
    x, y, w, h = [int(i) for i in bbox]
    roi = frame[y:y+h, x:x+w]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F) # edge 만들기
    focus_measure = laplacian.var()
    # blurred = cv2.Laplacian(cv2.GaussianBlur(gray_roi, (3, 3), 0), cv2.CV_64F) # gaussian blur 로 노이즈 제거 후 edge 만들기
    return focus_measure, laplacian

# 트래커 초기화
tracker = cv2.TrackerCSRT_create()
cap = cv2.VideoCapture(0)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
fps = cap.get(cv2.CAP_PROP_FPS) or 10
# out1 = cv2.VideoWriter('focusTest.mp4', fourcc, fps, (int(cap.get(3)), int(cap.get(4))))
# out2 = cv2.VideoWriter('edgeTest.mp4', fourcc, fps, (int(cap.get(3)), int(cap.get(4))))

init_bbox = None
tracking = False
best_score_saved = False
current_direction = 340
delEnc = 0
prev_score = 0
joystickWasRunning = False

print("Press SPACE to select the subject to track.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    key = cv2.waitKey(1) & 0xFF

    # ROI 선택 모드 (1회 실행)
    if key == ord(' ') and not tracking:
        init_bbox = cv2.selectROI("Frame", frame, fromCenter=False, showCrosshair=True)
        tracker.init(frame, init_bbox)
        tracking = True
        print("Tracking started...")

    # 추적 수행
    if tracking:
        success, bbox = tracker.update(frame)
        if success:
            x, y, w, h = [int(v) for v in bbox]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            score, edge_frame = is_roi_in_focus(frame, bbox)
            score = round(score, 0)
            cv2.putText(frame, f"Sharpness: {score:2.2f}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # focus 조절
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


            edge_frame = cv2.convertScaleAbs(edge_frame, alpha=3.0)
            cv2.imshow("Edge Detection", edge_frame)
            # out2.write(edge_frame)

        else:
            cv2.putText(frame, "Tracking failure", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

    # 화면 출력
    cv2.imshow("Frame", frame)
    # out1.write(frame)
    time.sleep(0.05)


    if key == ord('q'):
        break

cap.release()
# out1.release()
# out2.release()
cv2.destroyAllWindows()
