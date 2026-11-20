import cv2
import threading, queue
import time

cv2.namedWindow("Webcam Recording", flags=cv2.WINDOW_NORMAL)

# 웹캠 열기
# cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)  # 0은 기본 카메라 인덱스 macos
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # windows
if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    exit()

# # 녹화 파일 설정
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # 웹캠 너비
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # 웹캠 높이
fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30  # 웹캠 FPS (기본값: 30)

# # 저장할 파일 이름과 코덱 설정
output_filename = "webcam_recording.avi"
#fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 코덱 (XVID, MJPG, MP4V 등) macos
fourcc = cv2.VideoWriter_fourcc(*'DIVX')  # 코덱 (XVID, MJPG, MP4V 등) windows
out = cv2.VideoWriter(output_filename, fourcc, 60.0, (int(cap.get(3)), int(cap.get(4))))

print(f"녹화를 시작합니다. 저장 파일: {output_filename}")
frame_queue = queue.Queue(maxsize=256)  # 프레임을 저장할 큐

# 비디오 저장 함수
def save_frames(cap, out, frame_queue):
    while cap.isOpened():
        if not frame_queue.empty():
            frame = frame_queue.get()
            out.write(frame)
        else:
            # 영상 캡처가 종료된 경우 스레드를 종료합니다.
            if not cap.isOpened():
                break

save_thread = threading.Thread(target=save_frames, args=(cap, out, frame_queue))
save_thread.daemon = True # 메인 스레드 종료 시 함께 종료
save_thread.start()


# 비디오 캡처 루프
now = time.time()
frame_count = 0
fps_counter_start = 0.0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break
    now = time.time()
    # fps 계산
    frame_count += 1
    if time.time() - fps_counter_start >= 1.0:
        print(f"실시간 처리 FPS: {frame_count}")
        frame_count = 0
        fps_counter_start = time.time()

    # 현재 프레임의 너비(width), 높이(height) 구하기
    # height, width = frame.shape[:2]

    # 프레임 크기 조정 (예: 50% 크기로 줄이기)
    #cv2.resizeWindow("Webcam Recording", width=16*50, height=9*50)


    # 화면에 출력
    cv2.imshow("Webcam Recording", frame)
    frame_queue.put(frame)  # 프레임을 큐에 넣습니다.

    print("총 처리 시간: ", time.time() - now)
    # 'q'를 누르면 녹화 중지
    if cv2.waitKey(1) & 0xFF == 27:
        print("녹화를 종료합니다.")
        break

# 자원 해제
cap.release()
out.release()
print("총 녹화 시간: ", round(time.time()-now, 1))
cv2.destroyAllWindows()
save_thread.join()