
class AbsoluteEncoder
{
#define ENCODER_MIN_VAL 3  // min voltage: 0.015 / 5.0 * 1024 = 3
#define ENCODER_MAX_VAL 1021  // max voltage: 4.987 / 5.0 * 1024 = 1021
#define ENCODER_CROSSOVER_THRESHOLD 500
private:
    int analog_pin;
    int prev_enc_val;
    int curr_enc_val;
    double encoder_angle;
    int32_t rotations;
    bool is_reversed;
public:
    AbsoluteEncoder(int analog_pin) {
        this->analog_pin = analog_pin;
        encoder_angle = 0.0;
        prev_enc_val = 0;
        curr_enc_val = 0;
        rotations = 0;
        is_reversed = false;
    };

    void begin() {
        pinMode(analog_pin, INPUT);
    }

    void read()
    {
        prev_enc_val = curr_enc_val;
        if (is_reversed) {
            curr_enc_val = 1024 - analogRead(analog_pin);
        }
        else {
            curr_enc_val = analogRead(analog_pin);
        }
        encoder_angle = 360.0 * (curr_enc_val - ENCODER_MIN_VAL) / (ENCODER_MAX_VAL - ENCODER_MIN_VAL);

        if (curr_enc_val - prev_enc_val > ENCODER_CROSSOVER_THRESHOLD) {
            rotations--;
        }
        if (prev_enc_val - curr_enc_val > ENCODER_CROSSOVER_THRESHOLD) {
            rotations++;
        }
    };

    double getAngle() {
        return encoder_angle;
    };

    double getFullAngle() {
        return rotations * 360.0 + encoder_angle;
    };

    int32_t getRotations() {
        return rotations;
    };

    void reverse() {
        is_reversed = !is_reversed;
    }

};
