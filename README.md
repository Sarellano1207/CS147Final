# CS147Final
## A Smart Doorbell Prototype
   ### Note: 
   - I am currently planning to do a v2 or revamp of sorts. Upon revision there were some issues with design choice and even more from a walk-through perspective. TLDR in hindsight I'm not proud of this but at least there's something to fix rather than nothing.
   - To any recruiter/employer reading this, I hope you keep this in mind and extend some grace. If you see something that looks wrong, improper, or incorrect; trust me I know lol. I'm doing a different project in parallel to this so it may be a slow burn here.
   - Biggest thing I want to refactor is the replicability. The telegram API, the hardware, and server choice are the main culprits.
      - The telegram bot isn't working because I put the API key and deleted it. Now I want to make so it's a more distributed system and where I use environment variables instead of just plugging in the API key because I was running out of time on my final project (*yikes).
      - Second thing is the hardware. I don't really remember which LilyGo T Display ESP32 board i used, so I want to hone in on which board I will use and research which other boards can probably work here.
      - Third is the server choice. When I ran this I used an E2C AWS running on Ubuntu, but I want to see if it can work in other ways, say a raspberry pi server or another machine running the py script, etc.
      - AI has changed over the past 1-2 years so I want to update the object detection model. It ran OK, but I feel like it can be better now.
      - Will probably add a cmake file too. I've come to learn and appreciate cmake and can see this helping, especially when working with a bunch of different libraries and OSs. 


### Setup Instructions

#### 1. Modify Code for Your Machine

##### Server-side Changes:
1. **Update the `chat_id` in `server.py`:**
   - Navigate to the `serverside` folder.
   - Open `server.py` and go to line 43.
   - Send a message to the bot on Telegram https://t.me/SightSensebot (make a telegram account first if needed).
   - Visit https://api.telegram.org/bot7387450528:AAE4XznZMGa43fHU46KmcCoEBG4sSDU_q_o/getUpdates to get the `chat_id` from the result.
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
- Will update with a hardware list, but for now a LilyGO T-Display ESP32 and a OV2640/ArduCAM 2MP
