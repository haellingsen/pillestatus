import datetime
import time
import cv2
import numpy as np
import requests
import json

CAM_IP = "192.168.86.25"
USER_NAME = "admin"
PASSWORD = "asdf"
RTSP_URL = f"rtsp://{USER_NAME}:{PASSWORD}@{CAM_IP}/"

LOG_INTERVAL_S=60*5

THRESHOLD_MIN = 42
THRESHOLD_MAX = 255
THRESHOLD_AREA = 100000
MOVING_AVERAGE_WINDOW = 200


def get_weather_data():
    url = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=57.455&lon=10.226"


    headers = {
        'User-Agent': 'My User Agent 1.0',
        'sitename': "https://github.com/appselskapet"
    }

    response = requests.get(url, headers=headers)

    # Initialize a variable sitename with the name of your website and some contact info (e.g. a GitHub URL, a non-personal email address, a working website or a mobile app store appname). Do not fake this or you are likely to be permanently blacklisted!

    # Construct the Locationforecast URL with the necessary parameters. Always use HTTPS, as lots of unencrypted traffic can make you throttled or blocked.

    # Generate a Useragent object, with a custom User-Agent request header using the sitename variable as value. If this is missing or generic, you will get a 403 Forbidden response.
    # Call the request method of the Useragent object with the Locationforecast URL. For optimal performance, use a callback or promise which will enable you to continue running while the data is being downloaded (non-blocking I/O).
    # When the download is complete, check the HTTP Status header and handle each condition separately (see the Status Code documentation for specifics). In particular, pay special attention to the 203 (deprecated product) and 429 (throttling) statuses. Also check the Expires and Last-Modified timestamp headers (in RFC 1123 format), parse and store them in variables for later use.
    # If the result is a success (a 2xx status), send the request body to the JSON parser, which should return a suitable data structure for your programming language.
    # Before doing anything else, you should store the returned data structure in some semi-permanent local storage (e.g. on disk or an in-memory key-value store), along with the expires and last_modified timestamp variables above.
    # You can now process the forecast JSON data as necessary and present it to the user in a suitable fashion.
    # If, at a later time you want to repeat the request (e.g. the user has refreshed the page, or you want to update the data) you must first check if the current time is later than the expires value stored earlier; if not you must continue using the stored data. Do not send a new request every time the GPS position changes by a metre!

    # If the expires timestamp is in the past, you can repeat the request. However you should do this using the If-Modified-Since HTTP request header with the stored last_modified variable above as value. If the data has not been updated since your last request you will get a 304 Not Modified status code back with no body; you should then continue using the stored data until you get a 200 OK response.

    return response

def empty(value):
    pass


def hsv_mask_and_area(frame):
    print("Processing frame")
    # HSV mask
    lh = 42
    ls = 29
    lv = 3
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

    return frame_with_contours, convex_hull_contour_area, largest_contour_area


def process_image():
    vcap = get_video_capture()
    none_frame_counter = 0
    now = datetime.datetime.now()
    log_time = now
    areas = []
    areas_contour = []

    with open("/home/pi/pelletstat/log.txt", 'a', buffering=1) as f:
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
            masked_frame, area, area_contour = hsv_mask_and_area(masked_frame)
            areas.append(area)
            areas_contour.append(area_contour)
            area_moving_mean = int(sum(areas) / len(areas))
            area_contour_moving_mean = int(sum(areas_contour) / len(areas_contour))
            if len(areas) > MOVING_AVERAGE_WINDOW:
                areas.pop(0)
                areas_contour.pop(0)
            masked_frame = put_text(masked_frame, now, area_moving_mean)

#           print(areas)
#            cv2.imshow("", masked_frame)

            time.sleep(10)
            k = cv2.waitKey(1000) & 0xFF
            if k == ord('q'):
                vcap.release()
                cv2.destroyAllWindows()
                break
            time_to_log = now > log_time
            if time_to_log:
                f.write(f"{now.isoformat()}, {area_moving_mean}, {area}, {area_contour_moving_mean}, {area_contour}\n")
                # print(f"now: {now} next_log_time: {log_time.isoformat()}")
                log_time = log_time + datetime.timedelta(seconds=LOG_INTERVAL_S)
                cv2.imwrite("/home/pi/pelletstat/pellets.jpg", masked_frame)
                cv2.imwrite("/home/pi/pelletstat/"+str(now.isoformat()).replace(":","") + "_pellets.jpg", frame)


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
    print("getting video capture from " + CAM_IP)
    vcap = cv2.VideoCapture(RTSP_URL)
    vcap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)
    vcap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Check success
    if not vcap.isOpened():
        print("Could not open video device")
    return vcap


if __name__ == '__main__':
    process_image()
    #weather_data = get_weather_data()

#    if weather_data.status_code == 200:
 #       print(weather_data.json()["properties"]["timeseries"][0]["data"]["instant"]["details"]["air_temperature"])


