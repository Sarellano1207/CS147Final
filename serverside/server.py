# Import necessary libraries
from flask import Flask, request, jsonify
import numpy as np
import cv2
import tensorflow as tf
import os
from datetime import datetime
import requests

"""
- Run this in the terminal to actually run the server
$env:FLASK_APP = "server.py"
python -m flask run --host=0.0.0.0

- This is something to keep in mind. Basically it shows how we can use YOLOv3 as a better object detection model.
https://v-iashin.github.io/detector
"""

# Initialize Flask app
app = Flask(__name__)

# Define the path to the saved model
model_dir = "ssd_mobilenet_v2_fpnlite_320x320_coco17_tpu-8"
saved_model_path = os.path.join(model_dir, "saved_model")

# Load the pre-trained object detection model (SSD MobileNet V2)
model = tf.saved_model.load(saved_model_path)

# Get the labels for the object detection
label_map_path = "coco.names"
with open(label_map_path, "r") as f:
    LABELS = {i+1: line.strip() for i, line in enumerate(f.readlines())}

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

    # Close the image file
    photo.close()

    # Check if the message was sent successfully
    if response.status_code == 200:
        print("Notification sent successfully!")
    else:
        print("Failed to send notification.")

# Route to handle image upload
@app.route("/upload", methods=["POST"])
def receive_image():
    image_data = request.data
    filename = datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg"
    filepath = os.path.join("images", filename)

    # Save the image
    with open(filepath, "wb") as f:
        f.write(image_data)

    # Perform object detection
    image = cv2.imread(filepath)
    input_tensor = tf.convert_to_tensor(image)
    input_tensor = input_tensor[tf.newaxis, ...]
    detections = model(input_tensor)

    # Get detection information
    detection_scores = detections['detection_scores'][0].numpy()
    detection_classes = detections['detection_classes'][0].numpy().astype(np.int32)
    detection_boxes = detections['detection_boxes'][0].numpy()

    results = []
    for i in range(len(detection_scores)):
        if detection_scores[i] > 0.5:  # Confidence threshold
            class_id = detection_classes[i]
            class_name = LABELS.get(class_id, 'Unknown')
            class_score = detection_scores[i]
            class_box = detection_boxes[i].tolist()
            results.append({
                'class': class_name,
                'score': float(class_score),
                'box': class_box
            })

    # Send a notification to Telegram
    message = "Someone is at the door! Detected objects:"
    for result in results:
        message += f"\n{result['class']} - {result['score']}"
    send_telegram_message(message, filepath)

    return jsonify(results)

if __name__ == "__main__":
    if not os.path.exists("images"):
        os.makedirs("images")
    app.run(host="0.0.0.0", port=5000)
