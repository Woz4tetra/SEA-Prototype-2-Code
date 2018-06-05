#define BRAKE_CONTROL_PIN 6

#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include "AbsoluteEncoder.h"

#include "ArduinoFactoryBridge.h"

ArduinoFactoryBridge bridge("prototype2");
AbsoluteEncoder enc1(A0);
AbsoluteEncoder enc2(A1);

Adafruit_MotorShield AFMS = Adafruit_MotorShield();

Adafruit_DCMotor *motor = AFMS.getMotor(4);

int brake_val = 0;

void setup() {
    bridge.begin();

    bridge.writeHello();

    // MCUSR |= _BV(PUD);
    enc1.begin();
    enc2.begin();
    enc2.reverse();

    AFMS.begin();

    pinMode(BRAKE_CONTROL_PIN, OUTPUT);
    analogWrite(BRAKE_CONTROL_PIN, 0);

    enc1.read();
    enc2.read();
    bridge.setInitData("ff", enc1.getAngle(), enc2.getAngle());

    bridge.writeReady();
}

void setMotorSpeed(int speed) {
    if (speed > 0) {
        motor->run(FORWARD);
    }
    else if (speed < 0) {
        motor->run(BACKWARD);
    }
    motor->setSpeed(abs(speed));
}

void loop()
{
    enc1.read();
    enc2.read();

    if (!bridge.isPaused()) {
        bridge.write("enc", "ff", enc1.getFullAngle(), enc2.getFullAngle());
        delay(1);
    }

    if (bridge.available()) {
        int status = bridge.read();
        String command = bridge.getCommand();
        switch (status) {
            case 0:  // command
                switch (command.charAt(0)) {
                    case 'b':
                        brake_val = command.substring(1).toInt();
                        analogWrite(BRAKE_CONTROL_PIN, brake_val);
                        bridge.write("brake", "d", brake_val);  // echo value back
                        break;
                    case 'm': setMotorSpeed(command.substring(1).toInt()); break;
                }
                break;
            // case 1:  // start
            case 2:  // stop
                setMotorSpeed(0);
                analogWrite(BRAKE_CONTROL_PIN, 0);
                break;
        }

    }
}
