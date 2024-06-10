# Import necessary libraries
from flask import Flask, request, jsonify
import numpy as np
import cv2
import os
from datetime import datetime
import requests
import atexit
import matplotlib.pyplot as plt

# Initialize Flask app
app = Flask(__name__)

# Define the path to the Yolo model and the necessary files
yolo_dir = "yolo"
weights_path = os.path.join(yolo_dir, "yolov3.weights")
config_path = os.path.join(yolo_dir, "yolov3.cfg")
label_map_path = os.path.join(yolo_dir, "coco.names")

# Load the pre-trained object detection model
net = cv2.dnn.readNetFromDarknet(config_path, weights_path)

# Get the labels
with open(label_map_path, "r") as f:
    LABELS = [line.strip() for line in f.readlines()]

# Initialize counters for detected objects and the unknown objects
object_counts = {label: 0 for label in LABELS}
unknown = 0

# Function to send notification to Telegram
def send_telegram_message(message, photo_path):
    # Bot token ID received from BotFather on Telegram
    bot_token = "7387450528:AAE4XznZMGa43fHU46KmcCoEBG4sSDU_q_o"

    """ 
    IMPORTANT: Change this chat id with yours here or else you won't get notifications from Telegram
    """
    # Replace <YOUR_CHAT_ID> with your actual chat ID
    chat_id = "5027083991"

    # Set up the URL
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    # Open the image file
    photo = open(photo_path, 'rb')

    # Send the message and the photo
    data = {
        "chat_id": chat_id,
        "caption": message
    }
    files = {
        "photo": photo
    }

    response = requests.post(url, data=data, files=files)

    photo.close()

    # Check if the message was sent
    if response.status_code == 200:
        print("Notification sent successfully!")
    else:
        print("Failed to send notification.")

# Route to handle image upload
@app.route("/upload", methods=["POST"])
def receive_image():
    global object_counts
    global unknown
    image_data = request.data
    filename = datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg"
    filepath = os.path.join("images", filename)

    # Save the image
    with open(filepath, "wb") as f:
        f.write(image_data)

    # Perform object detection using YOLOv3
    image = cv2.imread(filepath)
    (H, W) = image.shape[:2]
    ln = net.getLayerNames()
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

    # Construct a blob from the input image and perform a forward pass
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    layerOutputs = net.forward(ln)

    # Initialize lists
    boxes = []
    confidences = []
    classIDs = []

    # Loop over each of the layer outputs
    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            # Filter out weak detections by ensuring the confidence is greater than a minimum threshold
            if confidence > 0.5:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

    # Apply suppression to suppress weak, overlapping bounding boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.3)

    detected_objects = []
    if len(idxs) > 0:
        for i in idxs.flatten():
            label = LABELS[classIDs[i]]
            object_counts[label] += 1  # Increment counter for detected object
            detected_objects.append(label)
    if len(detected_objects) == 0:
        unknown += 1

    # Send a notification to Telegram
    message = "Someone is at the door! Detected objects:"
    print(detected_objects)
    for obj in detected_objects:
        message += f"\n{obj}"
    send_telegram_message(message, filepath)

    return jsonify(detected_objects)

# Function to plot and save the data when the server session ends
def plot_and_save_data():
    labels = [label for label, count in object_counts.items() if count > 0]
    counts = [object_counts[label] for label in labels]

    if unknown > 0:
        labels.append('Unknown')
        counts.append(unknown)

    plt.figure(figsize=(10, 6))
    plt.bar(labels, counts)
    plt.xlabel('Detected Objects')
    plt.ylabel('Counts')
    plt.title('Detected Objects')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('detected_objects_plot.png')
    plt.close()

# Register the function to be called when the server session ends
atexit.register(plot_and_save_data)

if __name__ == "__main__":
    if not os.path.exists("images"):
        os.makedirs("images")
    app.run(host="0.0.0.0", port=5000)
