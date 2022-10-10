import datetime

import cv2
import imutils.contours
import matplotlib.pyplot as plt
import numpy as np


def empty(value):
    pass


if False:
    cv2.namedWindow("Params")
    cv2.createTrackbar("thresh", "Params", 50, 500, empty)
    cv2.createTrackbar("maxval", "Params", 255, 500, empty)
    cv2.createTrackbar("canny_thresh1", "Params", 50, 500, empty)
    cv2.createTrackbar("canny_thresh2", "Params", 255, 500, empty)
    cv2.createTrackbar("threshhold_area", "Params", 10000, 999999, empty)

THRESHOLD_MIN = 50
THRESHOLD_MAX = 255
THRESHOLD_AREA = 100000

def process_image():
    vcap = cv2.VideoCapture("rtsp://admin:asdf@192.168.86.25:554/")
    none_frame_counter = 0
    now = datetime.datetime.now()
    log_time = now

    with open("log.txt", 'a', buffering=1) as f:
        while 1:
            ret, frame = vcap.read()

            if frame is None:
                if none_frame_counter > 20:
                    none_frame_counter = 0

                    # retry connecting to the webcam
                    vcap = cv2.VideoCapture("rtsp://admin:asdf@192.168.86.25:554/")

                print("Frame was empty. Continue... none frame counter is: ")
                print(none_frame_counter)
                time.sleep(1)
                none_frame_counter += 1
                continue


            img_blur = cv2.bilateralFilter(frame, d=15, sigmaSpace=75, sigmaColor=75)
            img_gray = cv2.cvtColor(img_blur, cv2.COLOR_RGB2GRAY)
            # hist, bin_edges = np.histogram(img_gray, bins=256, range=(0, 256))
            # plt.plot(hist)
            # plt.show()

            _, thresh = cv2.threshold(img_gray, THRESHOLD_MIN, THRESHOLD_MAX, cv2.THRESH_BINARY)
            thresh_contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            thresh_contours = imutils.grab_contours(thresh_contours)
            (thresh_contours, _) = imutils.contours.sort_contours(thresh_contours)
            thresh_copy = frame.copy()

            if len(thresh_contours) != 0:
                c = max(thresh_contours, key=cv2.contourArea)
                area = cv2.contourArea(c)
                if area > THRESHOLD_AREA:
                    thresh = cv2.drawContours(thresh_copy, contours=c, contourIdx=-1, color=(255, 0, 0), thickness=2)

            # print(len(thresh_contours))

            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1.5
            fontColor = (0, 255, 0)
            thickness = 3
            lineType = 2

            text_to_put = str(f"{area:.0f}")

            textwidth = cv2.getTextSize(text_to_put,
                        font,
                        fontScale,
                        thickness)[0][0]

            bottomLeftCornerOfText = int(400), int(400)


            cv2.putText(thresh, text_to_put,
                        bottomLeftCornerOfText,
                        font,
                        fontScale,
                        fontColor,
                        thickness,
                        lineType)


            cv2.imshow("", thresh)

            k = cv2.waitKey(1) & 0xFF
            if k == ord('q'):
                cv2.destroyAllWindows()
                cv2.waitKey(1)

            now = datetime.datetime.now()
            current_pellet_area = str(f"{area:.0f}")
            if now > log_time:
                f.write(f"{now.isoformat()}, {current_pellet_area}\n")
                log_time = log_time + datetime.timedelta(seconds=10)
                # print(f"now: {now} next_log_time: {log_time.isoformat()}")


if __name__ == '__main__':
    process_image()

