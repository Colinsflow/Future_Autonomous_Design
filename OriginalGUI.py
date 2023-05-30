import tkinter as tk
import networkx as nx
import time
import pyrebase

config = {
    "apiKey": "",
    "authDomain": "",
    "databaseURL": "",
    "storageBucket": ""
}

image_width = 1520
image_height = 1296

start_time = time.time()
timer_status = False

firebase = pyrebase.initialize_app(config)
db = firebase.database()

intersections = [
    (1, 1), (1, 4), (1, 7), (1, 10),
    (4, 1), (4, 4), (4, 7), (4, 10),
    (7, 1), (7, 4), (7, 7), (7, 10),
    (10, 1), (10, 4), (10, 7), (10, 10)
]
orientation = {}
north = (3, 0)
south = (-3, 0)
west = (0, 3)
east = (0, -3)
orientation[east] = "east"
orientation[west] = "west"
orientation[south] = "south"
orientation[north] = "north"
beginOrientation = ""
pathToServer = []

direction = {}
northnorth = ("north", "north")
northeast = ("north", "east")
northwest = ("north", "west")
southsouth = ("south", "south")
southeast = ("south", "east")
southwest = ("south", "west")
easteast = ("east", "east")
eastnorth = ("east", "north")
eastsouth = ("east", "south")
westwest = ("west", "west")
westnorth = ("west", "north")
westsouth = ("west", "south")

direction[northnorth] = "straight"
direction[northeast] = "right"
direction[northwest] = "left"
direction[southsouth] = "straight"
direction[southeast] = "left"
direction[southwest] = "right"
direction[easteast] = "straight"
direction[eastnorth] = "left"
direction[eastsouth] = "right"
direction[westwest] = "straight"
direction[westnorth] = "right"
direction[westsouth] = "left"

G = nx.DiGraph()
G.add_edges_from([
    (1, 1), (1, 5), (2, 2), (2, 1), (3, 3), (3, 2), (3, 7), (4, 4), (4, 3), (5, 5), (5, 6), (5, 9), (6, 6), (6, 7),
    (6, 2), (7, 7),
    (7, 8), (7, 11), (8, 8), (8, 4), (9, 9), (9, 13), (10, 10), (10, 6), (10, 9), (11, 11), (11, 10), (11, 15),
    (12, 12), (12, 8), (12, 11), (13, 13), (13, 14), (14, 14), (14, 10), (14, 15), (15, 15), (15, 16), (16, 16),
    (16, 12)
])

car_entry = -1


def finishline():
    car_ID_entry = int(car_entry.get())
    path_ID_str = "path" + str(car_ID_entry)
    end_ID_str = "end" + str(car_ID_entry)
    stop_timer()
    clear_path(path_ID_str, end_ID_str)

def timer_update():
    global start_time, timer_status
    if timer_status:
        duration = int(time.time() - start_time)
        minutes = (duration // 60) % 60
        seconds = duration % 60
        timer.config(text=f"{minutes:02d}:{seconds:02d}")
    canvas.after(1000, timer_update)

def start_timer():
    global start_time, timer_status
    start_time = time.time()
    timer_status = True

def stop_timer():
    global timer_status
    timer_status = False

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
    return midpoint_x, midpoint_y

def get_square(x, y):
    """Return the square number that the point (x, y) belongs to."""
    row = y // 324  # each row is 1296 / 4 = 324 pixels high
    col = x // 380  # each column is 1520 / 4 = 380 pixels wide
    square_number = row * 4 + col + 1
    if square_number > 16:
        return None
    else:
        return square_number

def astar(end, car_entry):
    global beginOrientation
    global pathToServer
    print(car_entry)
    car_ID_str = "ID" + str(car_entry)
    start = int(db.child(car_ID_str).get().val().get("location").get("subsquare"))
    print(start)
    H = nx.shortest_path(G, source=(start), target=(end))

    path = []
    pp = []
    for x in H:
        path.append(intersections[x - 1])

    beginOrientation = orientation[path[0][0] - path[1][0], path[0][1] - path[1][1]]
    rng = range(1, (len(path) - 1))
    currOrientation = beginOrientation
    pp.append(beginOrientation)
    for x in rng:
        temp = orientation[path[x][0] - path[x + 1][0], path[x][1] - path[x + 1][1]]
        pp.append(direction[(currOrientation, temp)])
        currOrientation = temp
    pp += ['end']
    pathToServer = pp
    print(pathToServer)

    db.child("overhead").set({"path": pathToServer})
    return path

def clear_path(path_ID, end_ID):
    global pathToServer
    canvas.delete(path_ID)
    canvas.delete(end_ID)
    pathToServer = ""

def clear_all():
    global pathToServer
    canvas.delete("path8")
    canvas.delete("path5")
    canvas.delete("end5")
    canvas.delete("end8")
    canvas.delete("path6")
    canvas.delete("end6")
    pathToServer = ""
endflag = 0

def draw_path():
    global endflag
    # must grab intersection position from xy
    endflag = 1
    colorized = 'blue', 'green', 'red', 'white', 'cyan', 'yellow', 'magenta'

    end = int(input_entry.get())
    car_ID_entry = int(car_entry.get())
    path_ID_str = "path" + str(car_ID_entry)
    path_ID_color_str = colorized[int(car_ID_entry % 7)]
    end_ID_str = "end" + str(car_ID_entry)

    clear_path(path_ID_str, end_ID_str)
    path = astar(end, car_ID_entry)
    car_ID_str = "ID" + str(car_ID_entry)
    subsquare = int(db.child(car_ID_str).get().val().get("location").get("subsquare"))
    start2 = intersections[subsquare - 1]
    end = intersections[end - 1]
    new_path = [(y * 130 + 40, x * 110 + 10) for (x, y) in path]
    # Draw the path
    for i in range(len(new_path) - 1):
        x1, y1 = new_path[i]
        x2, y2 = new_path[i + 1]
        canvas.create_line(x1 * .5, y1 * .5, x2 * .5, y2 * .5, fill=path_ID_color_str, width=7, tags=path_ID_str)
    # Draw the start and end points
    # canvas.create_oval(start2[0]*-5, start2[1]*-5, start2[0]+5, start2[1]+5, fill="red")
    end = (end[1] * .5 * 130 + 20, end[0] * .5 * 110 + 5)
    canvas.create_oval(end[0] - 7, end[1] - 7, end[0] + 7, end[1] + 7, fill="green", tags=end_ID_str)
    path.insert(0, beginOrientation)
    start_timer()

    # picam2.start(show_preview=True)

ender = -1

# velocity = -1.0
# def velocityUpdate(message):
#     global velocity
#     velocity = message["data"]
#     # print(f"Global value updated: {velocity}")
#
# db.child("ID6").child("data").child("velocity").stream(velocityUpdate)
# print("stream initialized")

def update():
    global endflag, ender, x, dbData, velocity
    if endflag == 1:
        ender = int(input_entry.get())
        endflag = 0
    canvas.delete("polygon")
    # dbData = db.child("ID6").get().val()
    # x = dbData["aruco"]["corner1X"]
    # x = int(db.child("ID6").child("location").child("subsquare").get().val())
    data = db.child("ID6").get().val()
    corner1X = data["aruco"]["corner1X"] * .5
    corner1Y = data["aruco"]["corner1Y"] * .5
    corner2X = data["aruco"]["corner2X"] * .5
    corner2Y = data["aruco"]["corner2Y"] * .5
    frontX = data["aruco"]["frontX"] * .5
    frontY = data["aruco"]["frontY"] * .5
    X = data["location"]["X"] * .5
    Y = data["location"]["Y"] * .5
    subsquare = int(data["location"]["subsquare"])
    velocity = data["data"]["velocity"]
    # location = tk.Label(root, text=subsquare)
    # location.place(x=870, y=300)
    canvas.create_text(corner1X - 10, corner1Y - 10, text=6, fill="black", tags="polygon", width=30)

    canvas.create_polygon(corner1X, corner1Y, X, Y, corner2X, corner2Y, frontX, frontY, fill="blue", tags="polygon")

    canvas.create_text(880, 313, text=velocity, font=("Arial", 12), fill="white", tags="polygon")
    # for key,value in data.items():
    #    print(key,value)
    # velocityText = tk.Label(root, text=velocity)
    # velocityText.place(x=860, y=300)
    if subsquare == ender:
        finishline()
    root.after(1, update)

start = 1
thingy = intersections[start - 1]
start2 = (thingy[1] * 160 + 10, thingy[0] * 100 + 10)

root = tk.Tk()
root.title("GUI Control")
root.geometry("1920x1080")
# root.tk.call("tk", 'scaling', 4.0)

# Create the canvas to draw on
canvas = tk.Canvas(root, width=1920, height=1080)
canvas.pack(fill="both", expand=True)

# Draw the grid

# canvas.create_rectangle(0, 0, 1800, 1280, fill="light grey")

canvas.create_rectangle(55, 15, 705, 90, fill="grey")  # 65
canvas.create_rectangle(55, 185, 705, 260, fill="grey")  # 70
canvas.create_rectangle(55, 340, 705, 415, fill="grey")  # 75
canvas.create_rectangle(55, 520, 705, 595, fill="grey")  # 75

canvas.create_rectangle(55, 15, 135, 595, fill="grey")
canvas.create_rectangle(242.5, 15, 320, 595, fill="grey")
canvas.create_rectangle(425, 15, 505, 595, fill="grey")
canvas.create_rectangle(610, 15, 705, 595, fill="grey")

timer = tk.Label(root, text="00:00", font=("Arial", 15))
timer.place(x=800, y=400)

car_label = tk.Label(root, text="Car ID:", font=("Arial", 12))
car_label.place(x=800, y=50)

car_entry = tk.Entry(root, width=15)
car_entry.place(x=860, y=50)

destination_label = tk.Label(root, text="Destination:", font=("Arial", 12))
destination_label.place(x=770, y=90)

input_entry = tk.Entry(root, width=15)
input_entry.place(x=860, y=90)

destination_button = tk.Button(root, text="Submit", command=draw_path)
destination_button.place(x=840, y=150)

clear_button = tk.Button(root, text="Clear", command=clear_all)
clear_button.place(x=920, y=150)

velocityText = tk.Label(root, text="Velocity:")
velocityText.place(x=800, y=300)
canvas.create_text(910, 313, text="cm/s", font=("Arial", 12), fill="white")

update()
# velocityText = tk.Label(root, text=velocity)
# velocityText.place(x=860, y=300)
timer_update()
root.mainloop()

# Define the x and y ranges for each square

# Function to determine which square a point (x, y) belongs to