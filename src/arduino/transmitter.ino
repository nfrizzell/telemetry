#include <stdlib.h>
#include <SPI.h>
#include <RH_RF95.h>
#include <LiquidCrystal.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define RADIO_FREQUENCY 905.0
#define TRANSMIT_DELAY_MS 3000

struct RadioPacket
{
    float main_battery_voltage;
    float main_battery_amperage;
    float aux_battery_voltage;
    float ds18b20_temperature;
} packet;

enum Pins
{
    shunt_pin_1 = A5,
    shunt_pin_2 = A4,
    vdiv_48_pin = A3,
    vdiv_12_pin = A0,
    ds18b20_data = 5,
    rfm95_int = 2,
    rfm95_cs = 9,
    rfm95_rst = 10,
};

int starttime = millis();
char formattedPacket[RH_RF95_MAX_MESSAGE_LEN];
RH_RF95 rf95(Pins::rfm95_cs, Pins::rfm95_int);
OneWire oneWire(Pins::ds18b20_data);
DallasTemperature ds18b20(&oneWire);

void readDS18B20()
{
    ds18b20.requestTemperatures();

    packet.ds18b20_temperature = ds18b20.getTempCByIndex(0);
    Serial.println(packet.ds18b20_temperature);
}

void readAnalogData()
{
    float aux_voltage = analogRead(Pins::vdiv_12_pin);
    float main_voltage = analogRead(Pins::vdiv_48_pin);
    float shunt_pos = analogRead(Pins::shunt_pin_1);
    float shunt_neg = analogRead(Pins::shunt_pin_2);

    packet.aux_battery_voltage = ((aux_voltage/1024.0)*55.0);
    packet.main_battery_voltage = ((main_voltage/1024.0)*55.0);
    float shunt_voltage = (((shunt_pos - shunt_neg)/1024.0) * 5.0) / 101.0;
    packet.main_battery_amperage = shunt_voltage / 0.0001;
}

void readAllData()
{
    //readDS18B20();
    //readKY003();
    readAnalogData();

    // TBD
    packet.main_battery_voltage = 48.0;
    packet.main_battery_amperage = 100.0;

    char main_battery_voltage[10];
    char main_battery_amperage[10];
    char aux_battery_voltage[10];
    char ds18b20_temperature[10];

    dtostrf(packet.main_battery_voltage, 7, 3, main_battery_voltage);
    dtostrf(packet.main_battery_amperage, 7, 3, main_battery_amperage);
    dtostrf(packet.aux_battery_voltage, 7, 3, aux_battery_voltage);
    dtostrf(packet.ds18b20_temperature, 7, 3, ds18b20_temperature);

    memset(formattedPacket, 0, RH_RF95_MAX_MESSAGE_LEN);
    sprintf((char*)formattedPacket, "%s,%s,%s,%s,%d", main_battery_voltage, main_battery_amperage, aux_battery_voltage, ds18b20_temperature, (millis()-starttime)/1000);
}

void transmitData()
{
    Serial.println(formattedPacket);
    Serial.print("Sending "); Serial.println(formattedPacket); delay(10);
    rf95.send((uint8_t *)formattedPacket, sizeof(formattedPacket));

    Serial.println("Waiting for packet to complete..."); delay(10);
    rf95.waitPacketSent();
}

void setup()
{
    //pinMode(Pins::ky003_data, INPUT);
    pinMode(Pins::rfm95_rst, OUTPUT);

    digitalWrite(Pins::rfm95_rst, HIGH);
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
        Serial.println("Failed to set radio frequency.");
        while (1);
    }
}

void loop()
{
    readAllData();
    transmitData();
    delay(TRANSMIT_DELAY_MS);
}
