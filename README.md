# CS147Final
## A Smart Doorbell Prototype

### Setup Instructions

#### 1. Modify Code for Your Machine

##### Server-side Changes:
1. **Update the `chat_id` in `server.py`:**
   - Navigate to the `serverside` folder.
   - Open `server.py` and go to line 43.
   - Send a message to the bot on Telegram [here](https://t.me/SightSensebot).
   - Visit [this link](https://api.telegram.org/bot7387450528:AAE4XznZMGa43fHU46KmcCoEBG4sSDU_q_o/getUpdates) to get the `chat_id` from the result.
   - Replace the `chat_id` in the code with the one you obtained.

##### Board-related Changes:
2. **Update the `host` in `main.py`:**
   - Navigate to the `boardrelated` folder, then `Final_Project`, then `src`, then `main`.
   - Open `main.py` and go to line 198.
   - Replace the `host` with the IP address obtained when you run your Flask server. (You need to run the Flask server first to get the IP address.)

### Running the Project

1. **Run the Flask Server:**
   - Open a terminal (or Windows PowerShell) in the same directory as `server.py`.
   - Execute the following commands:
     ```sh
     $env:FLASK_APP = "server.py"
     python -m flask run --host=0.0.0.0
     ```

2. **Connect and Upload Code to the ESP32 Board:**
   - Ensure the ESP32 board is connected.
   - Use PlatformIO on Visual Studio Code (VSC) to open the project folder.
   - Upload and monitor the code.
     - If you encounter errors like SPI Interface error, try unplugging the board and uploading again.
     - If that doesn’t work, try disconnecting and reconnecting the pins.

3. **Testing the Setup:**
   - Once the Flask server is running and the code is uploaded to the board, let the board connect.
   - Press the button on the board.
   - The board will send a picture to the Flask server, which will then send the image and the object detection result to the Telegram chat.

### Notes
- Make sure you have all necessary dependencies installed for both the server and the board.
- Check your network settings to ensure the board can communicate with the server.
