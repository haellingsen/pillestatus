import datetime
import time

import cv2
import numpy as np

CAM_IP = "192.168.86.25"
USER_NAME = "admin"
PASSWORD = "asdf"
RTSP_URL = f"rtsp://{USER_NAME}:{PASSWORD}@{CAM_IP}/"
thresh1 = 0
thresh2 = 255

read_pic = False
read_web_cam = not read_pic

if read_pic:
    frame = cv2.imread("grabbed_frames/frame_2022-10-18T01:51:54.8.jpg")
else:
    if read_web_cam:
        cap = cv2.VideoCapture(RTSP_URL)
    else:
        cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Check success
    if not cap.isOpened():
        raise Exception("Could not open video device")

def passer(none):
    pass

cv2.namedWindow("p")
cv2.createTrackbar("lh", "p", 26, 179, passer)
cv2.createTrackbar("ls", "p", 20, 255, passer)
cv2.createTrackbar("lv", "p", 34, 255, passer)
cv2.createTrackbar("uh", "p", 179, 179, passer)
cv2.createTrackbar("us", "p", 255, 255, passer)
cv2.createTrackbar("uv", "p", 255, 255, passer)
cv2.createTrackbar("thresh1", "p", 0, 255, passer)
cv2.createTrackbar("thresh2", "p", 255, 255, passer)


def hsv_mask_and_area(frame):
    global ranges, frame_masked_inverted, _, frame_with_contours, thresh1, thresh2
    # HSV mask
    lh = cv2.getTrackbarPos("lh", "p")
    ls = cv2.getTrackbarPos("ls", "p")
    lv = cv2.getTrackbarPos("lv", "p")
    uh = cv2.getTrackbarPos("uh", "p")
    us = cv2.getTrackbarPos("us", "p")
    uv = cv2.getTrackbarPos("uv", "p")
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
    thresh1 = cv2.getTrackbarPos("thresh1", "p")
    thresh2 = cv2.getTrackbarPos("thresh2", "p")
    # Contours
    thresh = frame_masked_inverted_grey.copy()
    blurred = cv2
    ret, thresh = cv2.threshold(thresh, thresh1, thresh2, cv2.THRESH_BINARY)
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

while 1:
    if not read_pic:
        _, frame = cap.read()

    frame_with_contours, area = hsv_mask_and_area(frame)

    stacked = np.concatenate((frame, frame_with_contours), axis=1)
    cv2.imshow("stacked images", stacked)
    cv2.waitKey(1)
#    stacked_2 = np.concatenate((frame_masked_inverted_grey, canny_edge), axis=1)
#    cv2.imshow("stacked images 2", stacked_2)
#    cv2.waitKey(1)

    if frame is None:
        print("No frame grabbed.")
        time.sleep(1000)
        continue


    key = cv2.waitKey(10)
    if key == ord('s'):
        now = str(datetime.datetime.now().isoformat())[:-5]
        frame_name_stacked = f"stacked_{now}.jpg"
        frame_name = f"frame_{now}.jpg"
        print(f"Save frame to disk.\t  {frame_name} \n ranges: {ranges} \n Thresh1: {thresh1}, Thresh2: {thresh2}")
        cv2.imwrite("grabbed_frames/"+frame_name_stacked, stacked)
        cv2.imwrite("grabbed_frames/" + frame_name, frame)
        np.save(f"ranges_{now}.npy", ranges)

    elif key == ord('q'):
        cap.release()
        cv2.destroyAllWindows()
        break

