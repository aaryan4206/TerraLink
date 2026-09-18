#include <SPI.h>
#include <LoRa.h>

// =====================================================
// TERRALINK V1 - GATEWAY
// LoRa RECEIVER + DATA PARSER
// =====================================================

// ---------------- LoRa ----------------

#define LORA_FREQUENCY 433E6

#define LORA_SS    5
#define LORA_RST   14
#define LORA_DIO0  26

#define LORA_SCK   18
#define LORA_MISO  19
#define LORA_MOSI  23


// =====================================================
// SETUP
// =====================================================

void setup() {

  Serial.begin(115200);
  delay(1500);

  Serial.println();
  Serial.println();
  Serial.println("========================================");
  Serial.println("        TERRALINK V1 GATEWAY");
  Serial.println("========================================");


  // ===================================================
  // SPI
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


  Serial.println(
    "LoRa initialization : PASS"
  );


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
  // RECEIVER MODE
  // ===================================================

  LoRa.receive();


  Serial.println();
  Serial.println("Gateway radio : RX MODE");


  Serial.println();
  Serial.println("========================================");
  Serial.println("           GATEWAY READY");
  Serial.println("========================================");

  Serial.println();
  Serial.println("Waiting for Node sensor data...");
}


// =====================================================
// EXTRACT VALUE FROM FIELD
// =====================================================

String getValue(
  String field
) {

  int equalsPosition =
    field.indexOf('=');


  if (equalsPosition < 0) {

    return "";
  }


  return field.substring(
    equalsPosition + 1
  );
}


// =====================================================
// PROCESS SENSOR PACKET
// =====================================================

void processPacket(
  String packet
) {

  Serial.println();
  Serial.println();
  Serial.println("========================================");
  Serial.println("         SENSOR PACKET RECEIVED");
  Serial.println("========================================");


  // ===================================================
  // RAW PACKET
  // ===================================================

  Serial.print("Raw packet : ");
  Serial.println(packet);


  Serial.print("Packet size : ");
  Serial.println(packet.length());


  Serial.print("RSSI : ");
  Serial.print(
    LoRa.packetRssi()
  );
  Serial.println(" dBm");


  Serial.print("SNR  : ");
  Serial.print(
    LoRa.packetSnr()
  );
  Serial.println(" dB");


  // ===================================================
  // VALIDATE NODE PACKET
  // ===================================================

  if (!packet.startsWith("NODE=1")) {

    Serial.println();
    Serial.println("Packet type : UNKNOWN");
    Serial.println("Packet ignored.");

    LoRa.receive();

    return;
  }


  // ===================================================
  // PARSE PACKET
  // ===================================================

  int fieldStart = 0;

  int commaPosition = -1;


  String nodeID = "";
  String packetID = "";

  String temperatureString = "";
  String humidityString = "";
  String pressureString = "";
  String gasString = "";


  // ---------------------------------------------------
  // Go through each comma-separated field
  // ---------------------------------------------------

  while (fieldStart < packet.length()) {

    commaPosition =
      packet.indexOf(
        ',',
        fieldStart
      );


    String field;


    if (commaPosition == -1) {

      // Last field

      field =
        packet.substring(
          fieldStart
        );

      fieldStart =
        packet.length();
    }

    else {

      field =
        packet.substring(
          fieldStart,
          commaPosition
        );

      fieldStart =
        commaPosition + 1;
    }


    field.trim();


    // -------------------------------------------------
    // Identify field
    // -------------------------------------------------

    if (field.startsWith("NODE=")) {

      nodeID =
        getValue(field);
    }

    else if (field.startsWith("PKT=")) {

      packetID =
        getValue(field);
    }

    else if (field.startsWith("T=")) {

      temperatureString =
        getValue(field);
    }

    else if (field.startsWith("H=")) {

      humidityString =
        getValue(field);
    }

    else if (field.startsWith("P=")) {

      pressureString =
        getValue(field);
    }

    else if (field.startsWith("G=")) {

      gasString =
        getValue(field);
    }
  }


  // ===================================================
  // CONVERT VALUES
  // ===================================================

  int packetNumber =
    packetID.toInt();


  float temperature =
    temperatureString.toFloat();


  float humidity =
    humidityString.toFloat();


  float pressure =
    pressureString.toFloat();


  float gas =
    gasString.toFloat();


  // ===================================================
  // DISPLAY PARSED DATA
  // ===================================================

  Serial.println();
  Serial.println("PARSED SENSOR DATA");
  Serial.println("-------------------");


  Serial.print("Node ID       : ");
  Serial.println(nodeID);


  Serial.print("Packet number : ");
  Serial.println(packetNumber);


  Serial.print("Temperature   : ");
  Serial.print(
    temperature,
    2
  );
  Serial.println(" °C");


  Serial.print("Humidity      : ");
  Serial.print(
    humidity,
    2
  );
  Serial.println(" %");


  Serial.print("Pressure      : ");
  Serial.print(
    pressure,
    2
  );
  Serial.println(" hPa");


  Serial.print("Gas           : ");
  Serial.print(
    gas,
    2
  );
  Serial.println(" kOhm");


  // ===================================================
  // VALIDATION
  // ===================================================

  bool validPacket = true;


  if (nodeID != "1") {

    validPacket = false;
  }


  if (packetID == "") {

    validPacket = false;
  }


  if (temperatureString == "") {

    validPacket = false;
  }


  if (humidityString == "") {

    validPacket = false;
  }


  if (pressureString == "") {

    validPacket = false;
  }


  if (gasString == "") {

    validPacket = false;
  }


  Serial.println();


  if (validPacket) {

    Serial.println(
      "Sensor packet : VALID"
    );
  }

  else {

    Serial.println(
      "Sensor packet : INVALID"
    );
  }


  // ===================================================
  // RETURN TO RX
  // ===================================================

  LoRa.receive();


  Serial.println();
  Serial.println(
    "Gateway radio : RX MODE"
  );

  Serial.println(
    "Waiting for next sensor packet..."
  );

  Serial.println(
    "========================================"
  );
}


// =====================================================
// LOOP
// =====================================================

void loop() {

  int packetSize =
    LoRa.parsePacket();


  if (packetSize > 0) {

    String received = "";


    while (LoRa.available()) {

      received +=
        (char)LoRa.read();
    }


    processPacket(
      received
    );
  }


  delay(5);
}