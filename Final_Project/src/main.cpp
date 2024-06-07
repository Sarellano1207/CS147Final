#include <Arduino.h>
#include <HttpClient.h>
#include <WiFi.h>
#include <inttypes.h>
#include <stdio.h>
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs.h"
#include "nvs_flash.h"

#include <Wire.h>
#include <ArduCAM.h>
#include <SPI.h>
#include "memorysaver.h"

#define CS_PIN 33 // Adjust the CS pin according to your connection
#define BUTTON_PIN 32 // Pin where the button is connected

// This setup is defined in the AdruCAM library for the OV2640-Mini-2MP-PLUS Camera
#define OV2640_CHIPID_HIGH 0x0A
#define OV2640_CHIPID_LOW 0x0B
ArduCAM myCAM(OV2640, CS_PIN);

char ssid[50]; 
char pass[50];

// nvc_access is code from lab 4 and it grabs the wifi information from our apartment
// You would technically need to save a different ssid and password to get this working
void nvs_access() {
    // Initialize NVS
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        // NVS partition was truncated and needs to be erased
        // Retry nvs_flash_init
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    // Open
    Serial.printf("\n");
    Serial.printf("Opening Non-Volatile Storage (NVS) handle... ");
    nvs_handle_t my_handle;
    err = nvs_open("storage", NVS_READWRITE, &my_handle);
    if (err != ESP_OK) {
        Serial.printf("Error (%s) opening NVS handle!\n", esp_err_to_name(err));
    } else {
        Serial.printf("Done\n");
        Serial.printf("Retrieving SSID/PASSWD\n");
        size_t ssid_len = sizeof(ssid);
        size_t pass_len = sizeof(pass);
        err = nvs_get_str(my_handle, "ssid", ssid, &ssid_len);
        err |= nvs_get_str(my_handle, "pass", pass, &pass_len);
        switch (err) {
            case ESP_OK:
                Serial.printf("Done\n");
                Serial.printf("SSID = %s\n", ssid);
                Serial.printf("PASSWD = %s\n", pass);
                break;
            case ESP_ERR_NVS_NOT_FOUND:
                Serial.printf("The value is not initialized yet!\n");
                break;
            default:
                Serial.printf("Error (%s) reading!\n", esp_err_to_name(err));
        }
    }
    nvs_close(my_handle);
}

void setup() {
    Serial.begin(9600);
    Wire.begin();

    // Initialize SPI
    SPI.begin(25, 27, 26, 33); // SCK, MISO, MOSI, CS

    // Set CS pin as output and set high
    pinMode(CS_PIN, OUTPUT);
    digitalWrite(CS_PIN, HIGH);

    // Initialize the camera
    myCAM.write_reg(0x07, 0x80);
    delay(100);
    myCAM.write_reg(0x07, 0x00);
    delay(100);

    // Test SPI interface
    while (1) {
      myCAM.write_reg(ARDUCHIP_TEST1, 0x55);
      uint8_t temp = myCAM.read_reg(ARDUCHIP_TEST1);
      if (temp != 0x55) {
        Serial.println("SPI interface Error!");
        delay(1000);
      } else {
        Serial.println("SPI interface OK.");
        break;
      }
    }

    // Check if the camera module type is OV2640
    myCAM.set_format(BMP);
    myCAM.InitCAM();
    byte vid, pid;
    myCAM.wrSensorReg8_8(0xff, 0x01);
    myCAM.rdSensorReg8_8(OV2640_CHIPID_HIGH, &vid);
    myCAM.rdSensorReg8_8(OV2640_CHIPID_LOW, &pid);
    if ((vid != 0x26) || (pid != 0x42)) {
      Serial.println("Can't find OV2640 module!");
    } else {
      Serial.println("OV2640 detected.");
    }

    // Initialize the sensor
    myCAM.set_format(JPEG);
    myCAM.InitCAM();
    myCAM.OV2640_set_JPEG_size(OV2640_320x240);
    myCAM.clear_fifo_flag();
    
    // Grab SSID and Password
    delay(1000);
    nvs_access();
    delay(1000);

    // connect to wifi
    Serial.println();
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(ssid);
    WiFi.begin(ssid, pass);
    int attemptCount = 0;
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        attemptCount++;
        if (attemptCount > 60) { // 60 attempts of 500ms each equals 30 seconds
            Serial.println("Failed to connect to WiFi");
            return;
        }
    }
    
    // For debugging purposes 
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.println("MAC address: ");
    Serial.println(WiFi.macAddress());

    // Set the button pin as input
    pinMode(BUTTON_PIN, INPUT_PULLUP);
}

void loop() {
    if (digitalRead(BUTTON_PIN) == LOW) {
        Serial.println("Button Pressed!");
        // Set up camera to capture
        myCAM.flush_fifo();
        myCAM.clear_fifo_flag();
        myCAM.start_capture();
        Serial.println("Start capture");

        // Capture Image
        while (!myCAM.get_bit(ARDUCHIP_TRIG, CAP_DONE_MASK));
        Serial.println("Capture done.");

        // Print Image length for debugging purposes
        uint32_t length = myCAM.read_fifo_length();
        Serial.print("The length of the image is ");
        Serial.println(length, DEC);
        if (length >= MAX_FIFO_SIZE) {
            Serial.println("Over size.");
            return;
        } else if (length == 0) {
            Serial.println("Size is 0.");
            return;
        }

        // Allocated memory to save image information
        uint8_t *buffer = (uint8_t *)malloc(length);
        if (!buffer) {
            Serial.println("Memory allocation failed");
            return;
        }

        // Write image information to array
        myCAM.CS_LOW();
        myCAM.set_fifo_burst();
        for (uint32_t i = 0; i < length; i++) {
            buffer[i] = SPI.transfer(0x00);
        }
        myCAM.CS_HIGH();

        // Get variables ready for WIFI connection
        WiFiClient client;
        HttpClient http(client);
        char url[] = "/upload";
        char host[] = "192.168.0.13"; // Server IP address
        int port = 5000; // Server port

        Serial.println("Sending image data to server");

        // Actually send the image information
        http.beginRequest();
        http.post(host, port, url);
        http.sendHeader("Content-Type", "application/octet-stream");
        http.sendHeader("Content-Length", length);
        http.write(buffer, length); // Write image data directly
        http.endRequest();

        // Debugging purposes
        int statusCode = http.responseStatusCode();
        Serial.print("Status code: ");
        Serial.println(statusCode);

        if (statusCode == 200) {
            Serial.println("Image sent successfully");
        } else {
            Serial.println("Failed to send image");
        }

        // Free the buffer for the next image
        free(buffer);

        delay(1000); // Delay before the next iteration
    }
}
