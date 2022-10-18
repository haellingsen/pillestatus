import datetime
import time
import cv2
import numpy as np

CAM_IP = "192.168.86.25"
USER_NAME = "admin"
PASSWORD = "asdf"
RTSP_URL = f"rtsp://{USER_NAME}:{PASSWORD}@{CAM_IP}/"

THRESHOLD_MIN = 0
THRESHOLD_MAX = 255
THRESHOLD_AREA = 100000


def empty(value):
    pass


def hsv_mask_and_area(frame):
    # HSV mask
    lh = 26
    ls = 20
    lv = 34
    uh = 179
    us = 255
    uv = 255
    lower_range = np.array([lh, ls, lv])
    upper_range = np.array([uh, us, uv])
    ranges = np.array([lower_range, upper_range])
    frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    kernel = np.ones((5, 5), np.uint8)
    blur = cv2.blur(frame_hsv, (3, 3))
    mask = cv2.inRange(blur, lower_range, upper_range)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.dilate(mask, kernel, iterations=1)
    frame_masked = cv2.bitwise_and(frame, frame, mask=mask)
    mask_inverted = 255 - mask
    frame_masked_inverted = cv2.bitwise_and(frame, frame, mask=mask_inverted)
    frame_masked_inverted_grey = cv2.cvtColor(frame_masked_inverted, cv2.COLOR_HSV2BGR)
    frame_masked_inverted_grey = cv2.cvtColor(frame_masked_inverted_grey, cv2.COLOR_BGR2GRAY)
    # Contours
    thresh = frame_masked_inverted_grey.copy()
    blurred = cv2
    ret, thresh = cv2.threshold(thresh, THRESHOLD_MIN, THRESHOLD_MAX, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    frame_with_contours = frame.copy()
    largest_contour_area = largest_contour_area = 0
    if len(contours) != 0:
        largest_contour = max(contours, key=cv2.contourArea)
        convex_hull_contour = cv2.convexHull(largest_contour, False)

        largest_contour_area = cv2.contourArea(largest_contour)
        convex_hull_contour_area = cv2.contourArea(convex_hull_contour)

        if convex_hull_contour_area > 100000:
            frame_with_contours = cv2.drawContours(frame_with_contours, [largest_contour], 0, (0, 255, 0), 2)
            frame_with_contours = cv2.drawContours(frame_with_contours, [convex_hull_contour], 0, (0, 0, 255), 2)

    return frame_with_contours, convex_hull_contour_area


def process_image():
    vcap = get_video_capture()
    none_frame_counter = 0
    now = datetime.datetime.now()
    log_time = now
    areas = []

    with open("log.txt", 'a', buffering=1) as f:
        while 1:
            ret, frame = vcap.read()

            if frame is None:
                if none_frame_counter > 20:
                    none_frame_counter = 0
                    # retry connecting to the webcam
                    vcap.release()
                    time.sleep(5)
                    vcap = get_video_capture()

                print("Frame was empty. Continue... none frame counter is: ")
                print(none_frame_counter)
                time.sleep(1)
                none_frame_counter += 1
                continue

            now = datetime.datetime.now()
            masked_frame = frame.copy()
            masked_frame, area = hsv_mask_and_area(masked_frame)
            areas.append(area)
            area_moving_mean = int(sum(areas) / len(areas))
            if len(areas) > 50: areas.pop(0)
            masked_frame = put_text(masked_frame, now, area_moving_mean)

#           print(areas)
#            cv2.imshow("", masked_frame)

            time.sleep(10)
            k = cv2.waitKey(1000) & 0xFF
            if k == ord('q'):
                vcap.release()
                cv2.destroyAllWindows()
                break

            if now > log_time:
                f.write(f"{now.isoformat()}, {area_moving_mean}, {area}\n")
                log_time = log_time + datetime.timedelta(seconds=300)
                # print(f"now: {now} next_log_time: {log_time.isoformat()}")
                cv2.imwrite("pellets.jpg", masked_frame)


def put_text(frame, now, area):
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 1.5
    fontColor = (0, 255, 0)
    thickness = 3
    lineType = 2
    text_to_put = str(f"{area:.0f} {str(now.isoformat())[:-7]}")
    textwidth = cv2.getTextSize(text_to_put,
                                font,
                                fontScale,
                                thickness)[0][0]
    bottomLeftCornerOfText = int(50), int(50)
    cv2.putText(frame, text_to_put,
                bottomLeftCornerOfText,
                font,
                fontScale,
                fontColor,
                thickness,
                lineType)
    return frame


def get_video_capture():
    vcap = cv2.VideoCapture(RTSP_URL)
    vcap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)
    vcap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Check success
    if not vcap.isOpened():
        print("Could not open video device")
    return vcap


if __name__ == '__main__':
    process_image()
