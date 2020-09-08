#include <stdlib.h>
#include <SPI.h>
#include <RH_RF95.h>
#include <LiquidCrystal.h>

#define RADIO_FREQUENCY 905.5
#define TIMEOUT_MS 5000

struct SerialData
{
    float main_battery_voltage;
    float main_battery_amperage;
    float aux_battery_voltage;
    float dht11_temperature;
    int rpm;
} packet;

enum Pins
{
    rfm95_rst = 10,
    rfm95_int = 2,
    rfm95_cs = 9,
};

char serialBuffer[RH_RF95_MAX_MESSAGE_LEN];
RH_RF95 rf95(Pins::rfm95_cs, Pins::rfm95_int);

void receiveData()
{
    Serial.println("Waiting for packet..."); delay(10);
    if (rf95.waitAvailableTimeout(TIMEOUT_MS))
    {
        if (rf95.recv(serialBuffer, RH_RF95_MAX_MESSAGE_LEN))
        {
            // Append RSSI to data packet to be sent
            char rssi[10];
            dtostrf(rf95.lastRssi(), 7, 3, rssi);
            strcat(serialBuffer, ",");
            strcat(serialBuffer, rssi);

            // Write data packet over serial port, where it will be parsed
            Serial.println(serialBuffer);
        }

        else
        {
            Serial.println("Receive failed");
        }
    }
    else
    {
        Serial.println("No packet received.");
    }
}

void setup()
{
    pinMode(Pins::rfm95_rst, OUTPUT);
    digitalWrite(Pins::rfm95_rst, HIGH);
    while (!Serial);
    Serial.begin(9600);
    delay(100);

    // Setup radio
    // manual reset
    digitalWrite(Pins::rfm95_rst, LOW);
    delay(10);
    digitalWrite(Pins::rfm95_rst, HIGH);
    delay(10);

    while (!rf95.init())
    {
        Serial.println("Failed to initialize LoRa radio.");
        while (1);
    }

    Serial.println("LoRa radio initialized successfully.");

    if (!rf95.setFrequency(RADIO_FREQUENCY))
    {
        Serial.println("setFrequency failed");
        while (1);
    }
    rf95.setTxPower(23, false);
}

void loop()
{
    receiveData();
    delay(100);
}
