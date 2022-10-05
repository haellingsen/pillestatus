import datetime

import imutils
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import cv2
import numpy as np
import matplotlib.pyplot as plt


def main(thresh_1=10, thresh_2=100):
    vcap = cv2.VideoCapture("rtsp://admin:asdf@192.168.86.25:554/")

    now = datetime.datetime.now()
    log_time = now

    with open("log.txt", 'a', buffering=1) as f:
       while 1:
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            cv2.destroyAllWindows()
            cv2.waitKey(1)
            break
        elif k == ord('u'):
            thresh_1+=10
            print(thresh_1)
        elif k == ord('j'):
            thresh_1 -= 10
            print(thresh_1)
        elif k == ord('i'):
            thresh_2 += 10
            print(thresh_2)
        elif k == ord('k'):
            thresh_2 -= 10
            print(thresh_2)

        ret, frame = vcap.read()

        if frame is None:
            print("Frame was empty. Continue...")
            continue


        img_blur = cv2.bilateralFilter(frame, d=15, sigmaSpace=75, sigmaColor=75)
        #img_blur = cv2.GaussianBlur(img, (7, 7), 0)
        img_gray = cv2.cvtColor(img_blur, cv2.COLOR_RGB2GRAY)
        a = img_gray.max()
        #print(a)
        _, thresh = cv2.threshold(img_gray, a / 2 - 30, a, cv2.THRESH_BINARY)

        contours_, hierarchy = cv2.findContours(
            image=thresh,
            mode=cv2.RETR_TREE,
            method=cv2.CHAIN_APPROX_SIMPLE)

        # Sort the contours
        contours_ = sorted(contours_, key=cv2.contourArea, reverse=True)

        # Draw the contour
        img_copy = frame.copy()
        final = cv2.drawContours(img_copy, contours_, contourIdx=-1,
                                 color=(255, 0, 0), thickness=2)


        # The first order of the contours
        c_0 = contours_[0]

        big_contour = max(c_0, key=cv2.contourArea)

        # image moment
        M = cv2.moments(c_0)
        #print(M.keys())


        # test from https://pyimagesearch.com/2016/04/04/measuring-distance-between-objects-in-an-image-with-opencv/
        edged = cv2.Canny(img_gray, thresh_1, thresh_2)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)

        # find contours in the edge map
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        # sort the contours from left-to-right and, then initialize the
        # distance colors and reference object
        (cnts, _) = contours.sort_contours(cnts)

        img_copy = frame.copy()
        edged = cv2.drawContours(img_copy, contours=cnts,
                                     contourIdx=-1,
                                     color=(255, 0, 0), thickness=2)




        # The centroid point
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])

        # The extreme points
        l_m = tuple(c_0[c_0[:, :, 0].argmin()][0])
        r_m = tuple(c_0[c_0[:, :, 0].argmax()][0])
        t_m = tuple(c_0[c_0[:, :, 1].argmin()][0])
        b_m = tuple(c_0[c_0[:, :, 1].argmax()][0])
        pst = [l_m, r_m, t_m, b_m]
        xcor = [p[0] for p in pst]
        ycor = [p[1] for p in pst]

        # Plot the points
        # plt.figure(figsize=(16, 8))
        # plt.subplot(3, 2, 1)
        # plt.imshow(img_gray, cmap='gray')
        # plt.scatter([cx], [cy], c='b', s=50)
        # plt.subplot(3, 2, 2)
        # plt.imshow(img_gray, cmap='gray')
        # plt.scatter(xcor, ycor, c='b', s=50)
     #   plt.waitforbuttonpress(1)

        # The first order of the contours
        c_0 = contours_[0]
        # Get the 4 points of the bounding rectangle
        x, y, w, h = cv2.boundingRect(c_0)
        # Draw a straight rectangle with the points
        img_copy = frame.copy()
        img_box = cv2.rectangle(img_copy, (x, y), (x + w, y + h), color=(255, 0, 0), thickness=2)

        # Get the 4 points of the bounding rectangle with the minimum area
        rect = cv2.minAreaRect(c_0)
        current_area = rect[1][0]*rect[1][1]
        box = cv2.boxPoints(rect)
        box = box.astype('int')
        # Draw a contour with the points
        img_copy = frame.copy()
        img_box_2 = cv2.drawContours(img_copy, contours=[box],
                                     contourIdx=-1,
                                     color=(255, 0, 0), thickness=2)

        # plt.subplot(3, 2, 3);
        # plt.imshow(img_box)
        # plt.subplot(3, 2, 4);
        # plt.imshow(img_box_2)

        # Detect the convex contour
        hull = cv2.convexHull(c_0)
        img_copy = frame.copy()
        img_hull = cv2.drawContours(img_copy, contours=[hull],
                                    contourIdx=0,
                                    color=(255, 0, 0), thickness=2)
        # plt.subplot(3, 2, 5)
        # plt.imshow(img_hull)
        # plt.waitforbuttonpress(1)
        #
        # f, axarr = plt.subplots(2, 2, figsize=(16, 8))
        # axarr[0, 0].imshow(img_blur)
        # axarr[0, 1].imshow(img_gray)
        # axarr[1, 0].imshow(thresh, cmap='gray')
        # axarr[1, 1].imshow(final)
        # plt.waitforbuttonpress(1)
        # input()

        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 1.5
        fontColor = (0, 255, 0)
        thickness = 3
        lineType = 2

        text_to_put = str(f"{current_area:.0f}")
        text_to_put_convex_hull = str(f"{cv2.contourArea(big_contour):.0f}")

        textwidth = cv2.getTextSize(text_to_put,
                    font,
                    fontScale,
                    thickness)[0][0]

        bottomLeftCornerOfText = int(x + w/2 - textwidth/2), int(y + h/2)


        cv2.putText(img_box_2, text_to_put,
                    bottomLeftCornerOfText,
                    font,
                    fontScale,
                    fontColor,
                    thickness,
                    lineType)

        cv2.putText(edged, text_to_put_convex_hull,
                    bottomLeftCornerOfText,
                    font,
                    fontScale,
                    fontColor,
                    thickness,
                    lineType)



        # concatenate image Horizontally
        hori = np.concatenate((final, edged, img_box_2), axis=1)
        cv2.imshow('VIDEO', hori)
        cv2.waitKey(1)

        now = datetime.datetime.now()
        current_pellet_area=str(f"{current_area:.0f}")
        if now > log_time:
            f.write(f"{now.isoformat()}, {current_pellet_area}\n")
            log_time = log_time + datetime.timedelta(seconds=10)
            print(f"now: {now} log_time: {log_time.isoformat()}")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
