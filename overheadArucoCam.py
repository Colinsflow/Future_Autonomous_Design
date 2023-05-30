import cv2
from cv2 import aruco
from libcamera import controls
from picamera2 import MappedArray, Picamera2, Preview
import time
import pyrebase
config = {
    "apiKey" : "",
    "authDomain" : "",
    "databaseURL" : ",
    "storageBucket" : ""
    }

firebase = pyrebase.initialize_app(config)
db = firebase.database()


def get_traffic_square(x, y):
    """Return the square number that the point (x, y) belongs to."""
    #y mid = 671 x mid = 765
    if y > 305 and y < 765:
        if y > 424 and y < 548:
            if x > 470 and x < 648: #modded
                return 7
        if x > 270 and x < 648:
            return 6
    if y > 250 and y < 602:
        if y > 445 and y < 602:
            if x >837 and x < 996:
                return 11
        if x >= 648 and x < 996:
            return 7
    if y > 588 and y < 948:
        if y > 745 and y < 948 :
            if x >= 846 and x < 1000:
                return 10
        if x > 846 and x < 1210:
            return 11
    if y >= 660 and y < 1129:
        if y >= 745 and y < 951:
            if x > 473 and x < 642:
                return 6
        if x > 473 and x < 846:
            return 10
    return 0


def get_square(x, y):
    """Return the square number that the point (x, y) belongs to."""
    row = y // 324  # each row is 1296 / 4 = 324 pixels high
    col = x // 380  # each column is 1520 / 4 = 380 pixels wide
    square_number = row * 4 + col + 1
    if square_number > 16:
        return None
    else:
        return square_number
    
def get_midpoint(corner1, corner2, corner3, corner4):
    """Return the midpoint of a polygon with four corners."""
    midpoint1_x = (corner1[0] + corner2[0]) / 2
    midpoint1_y = (corner1[1] + corner2[1]) / 2
    midpoint2_x = (corner2[0] + corner3[0]) / 2
    midpoint2_y = (corner2[1] + corner3[1]) / 2
    midpoint3_x = (corner3[0] + corner4[0]) / 2
    midpoint3_y = (corner3[1] + corner4[1]) / 2
    midpoint4_x = (corner4[0] + corner1[0]) / 2
    midpoint4_y = (corner4[1] + corner1[1]) / 2
    midpoint_x = (midpoint1_x + midpoint2_x + midpoint3_x + midpoint4_x) / 4
    midpoint_y = (midpoint1_y + midpoint2_y + midpoint3_y + midpoint4_y) / 4
    front_mid_pos = ((corner3[0] + corner4[0]) / 2,(corner3[1] + corner4[1])/2)
    return midpoint_x, midpoint_y, front_mid_pos
    
def update():
    
    #start_time = time.time()

    
    
    frame = picam2.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    markerCorners, markerIds, rejectedCandidates = detector.detectMarkers(gray)
    #print("--- %s seconds framecap markers---" % (time.time() - start_time))
    
    
    
    for j in range(len(markerCorners)):
        #get car ID
        car_ID = int(markerIds[j])
        if(car_ID != 6 and car_ID !=  8):
            break
        car_str = "ID" + str(car_ID)
        corner1 = markerCorners[j][0][0]
        corner2 = markerCorners[j][0][1]
        corner3 = markerCorners[j][0][2]
        corner4 = markerCorners[j][0][3]
        midpoint = get_midpoint(corner1, corner2, corner3, corner4)
        subsquare = get_square(midpoint[0],midpoint[1])
        traffic_square = get_traffic_square(midpoint[0],midpoint[1])
#         car_str = "ID_5"
        tmp = car_str + "/location/"
        tmp2 = car_str +"/aruco/"
        data = {
            tmp: {
                "X": midpoint[0],
                "Y": midpoint[1],
                "subsquare":subsquare,
                "traffic sensor":traffic_square
            },
            tmp2: {
                "corner1X":int(corner1[0]),
                "corner1Y":int(corner1[1]),
                "corner2X":int(corner2[0]),
                "corner2Y":int(corner2[1]),
                "frontX":midpoint[2][0],
                "frontY":midpoint[2][1]
            }
        }
        db.update(data)
#             db.child("traxxas").child(car_str).update({"X":midpoint[0]})
#             db.child("traxxas").child(car_str).update({"Y":midpoint[1]})
#             db.child("traxxas").child(car_str).update({"frontX":midpoint[2][0]})
#             db.child("traxxas").child(car_str).update({"frontY":midpoint[2][1]})
        
        #print(markerCorners[j][0][0][0],markerCorners[j][0][0][1])
#             db.child("traxxas").child("ID8").update({"X":int(markerCorners[j][0][0][0])})
#             db.child("traxxas").child("ID8").update({"Y":int(markerCorners[j][0][0][1])})
    #print("--- %s seconds sent to firebase---" % (time.time() - start_time))
# Create the GUI window
picam2 = Picamera2()
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
# picam2.start_preview(Preview.QTGL)
#picam2.title_fields = ["Hey"]
camera_config = picam2.create_preview_configuration(main={"size": (1520, 1296)})#{"size": (1920, 1080)})
picam2.configure(camera_config)
picam2.start()
     
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
detectorParams = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(dictionary, detectorParams)
while True:
    update()      
