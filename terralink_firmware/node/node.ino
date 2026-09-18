#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>

// =====================================================
// TERRALINK V1 - NODE
// BME680 SENSOR + LoRa TRANSMITTER
// =====================================================

// ---------------- LoRa ----------------

#define LORA_FREQUENCY 433E6

#define LORA_SS    5
#define LORA_RST   14
#define LORA_DIO0  26

#define LORA_SCK   18
#define LORA_MISO  19
#define LORA_MOSI  23

// ---------------- BME680 ----------------

#define BME_SDA 21
#define BME_SCL 22

// ---------------- Timing ----------------

#define TRANSMISSION_INTERVAL 5000


// =====================================================
// OBJECTS
// =====================================================

Adafruit_BME680 bme;

bool bmeAvailable = false;

unsigned long packetNumber = 0;


// =====================================================
// SETUP
// =====================================================

void setup() {

  Serial.begin(115200);
  delay(1500);

  Serial.println();
  Serial.println();
  Serial.println("========================================");
  Serial.println("          TERRALINK V1 NODE");
  Serial.println("========================================");


  // ===================================================
  // BME680 INITIALIZATION
  // ===================================================

  Serial.println();
  Serial.println("Initializing BME680...");

  Wire.begin(
    BME_SDA,
    BME_SCL
  );


  // Try 0x76 first

  if (bme.begin(0x76)) {

    bmeAvailable = true;

    Serial.println("BME680 found at address 0x76");
  }

  // Try 0x77

  else if (bme.begin(0x77)) {

    bmeAvailable = true;

    Serial.println("BME680 found at address 0x77");
  }

  else {

    bmeAvailable = false;

    Serial.println("WARNING: BME680 NOT FOUND");
    Serial.println("Node will continue without sensor.");
  }


  // ===================================================
  // BME680 CONFIGURATION
  // ===================================================

  if (bmeAvailable) {

    bme.setTemperatureOversampling(
      BME680_OS_8X
    );

    bme.setHumidityOversampling(
      BME680_OS_2X
    );

    bme.setPressureOversampling(
      BME680_OS_4X
    );

    bme.setIIRFilterSize(
      BME680_FILTER_SIZE_3
    );

    bme.setGasHeater(
      320,
      150
    );

    Serial.println("BME680 configuration : PASS");
  }


  // ===================================================
  // SPI INITIALIZATION
  // ===================================================

  Serial.println();
  Serial.println("Initializing SPI...");

  SPI.begin(
    LORA_SCK,
    LORA_MISO,
    LORA_MOSI,
    LORA_SS
  );

  Serial.println("SPI : PASS");


  // ===================================================
  // LORA INITIALIZATION
  // ===================================================

  Serial.println();
  Serial.println("Initializing LoRa...");

  LoRa.setPins(
    LORA_SS,
    LORA_RST,
    LORA_DIO0
  );


  if (!LoRa.begin(LORA_FREQUENCY)) {

    Serial.println();
    Serial.println("ERROR: LoRa initialization FAILED");

    while (true) {

      delay(1000);

      Serial.println(
        "LoRa not detected..."
      );
    }
  }


  Serial.println("LoRa initialization : PASS");


  // ===================================================
  // LORA CONFIGURATION
  // ===================================================

  LoRa.setTxPower(17);

  LoRa.setSpreadingFactor(7);

  LoRa.setSignalBandwidth(125E3);

  LoRa.setCodingRate4(5);

  LoRa.enableCrc();


  Serial.println();
  Serial.println("LoRa configuration");
  Serial.println("-------------------");

  Serial.print("Frequency : ");
  Serial.print(
    LORA_FREQUENCY / 1000000.0
  );
  Serial.println(" MHz");

  Serial.println("TX Power  : 17 dBm");
  Serial.println("SF        : 7");
  Serial.println("Bandwidth : 125 kHz");
  Serial.println("Coding    : 4/5");
  Serial.println("CRC       : ENABLED");


  // ===================================================
  // NODE READY
  // ===================================================

  LoRa.idle();

  Serial.println();
  Serial.println("========================================");
  Serial.println("             NODE READY");
  Serial.println("========================================");

  Serial.println();
  Serial.println("Operating mode:");
  Serial.println("READ SENSOR -> TRANSMIT -> WAIT");

  Serial.println();
  Serial.print("Transmission interval : ");
  Serial.print(
    TRANSMISSION_INTERVAL / 1000
  );
  Serial.println(" seconds");
}


// =====================================================
// READ BME680
// =====================================================

bool readSensor(
  float &temperature,
  float &humidity,
  float &pressure,
  float &gas
) {

  // ---------------------------------------------------
  // Sensor unavailable
  // ---------------------------------------------------

  if (!bmeAvailable) {

    temperature = -1;
    humidity = -1;
    pressure = -1;
    gas = -1;

    return false;
  }


  // ---------------------------------------------------
  // Perform measurement
  // ---------------------------------------------------

  if (!bme.performReading()) {

    Serial.println(
      "BME680 reading : FAILED"
    );

    temperature = -1;
    humidity = -1;
    pressure = -1;
    gas = -1;

    return false;
  }


  // ---------------------------------------------------
  // Store values
  // ---------------------------------------------------

  temperature =
    bme.temperature;

  humidity =
    bme.humidity;

  pressure =
    bme.pressure / 100.0;

  gas =
    bme.gas_resistance / 1000.0;


  return true;
}


// =====================================================
// SEND SENSOR DATA
// =====================================================

void transmitSensorData() {

  packetNumber++;


  Serial.println();
  Serial.println();
  Serial.println("========================================");

  Serial.print("          SENSOR PACKET #");
  Serial.println(packetNumber);

  Serial.println("========================================");


  // ===================================================
  // READ SENSOR
  // ===================================================

  float temperature;
  float humidity;
  float pressure;
  float gas;


  bool sensorOK = readSensor(
    temperature,
    humidity,
    pressure,
    gas
  );


  // ===================================================
  // DISPLAY SENSOR DATA
  // ===================================================

  Serial.println();
  Serial.println("BME680 READINGS");
  Serial.println("-------------------");


  Serial.print("Temperature : ");
  Serial.print(
    temperature,
    2
  );
  Serial.println(" °C");


  Serial.print("Humidity    : ");
  Serial.print(
    humidity,
    2
  );
  Serial.println(" %");


  Serial.print("Pressure    : ");
  Serial.print(
    pressure,
    2
  );
  Serial.println(" hPa");


  Serial.print("Gas         : ");
  Serial.print(
    gas,
    2
  );
  Serial.println(" kOhm");


  if (sensorOK) {

    Serial.println(
      "Sensor reading : PASS"
    );
  }

  else {

    Serial.println(
      "Sensor reading : FAILED"
    );
  }


  // ===================================================
  // CREATE DATA PACKET
  // ===================================================

  String packet =
    "NODE=1"
    ",PKT=" + String(packetNumber) +
    ",T=" + String(temperature, 2) +
    ",H=" + String(humidity, 2) +
    ",P=" + String(pressure, 2) +
    ",G=" + String(gas, 2);


  Serial.println();
  Serial.print("Packet : ");
  Serial.println(packet);


  // ===================================================
  // TRANSMIT
  // ===================================================

  Serial.println();
  Serial.println("LoRa transmission starting...");


  LoRa.idle();

  delay(50);


  LoRa.beginPacket();

  LoRa.print(packet);


  int result =
    LoRa.endPacket();


  // ===================================================
  // TRANSMISSION RESULT
  // ===================================================

  if (result == 1) {

    Serial.println(
      "LoRa transmission : PASS"
    );
  }

  else {

    Serial.println(
      "LoRa transmission : FAILED"
    );
  }


  Serial.println();
  Serial.println(
    "Gateway does not send ACK in V1."
  );


  // ===================================================
  // RETURN TO IDLE
  // ===================================================

  LoRa.idle();
}


// =====================================================
// LOOP
// =====================================================

void loop() {

  transmitSensorData();

  delay(
    TRANSMISSION_INTERVAL
  );
}