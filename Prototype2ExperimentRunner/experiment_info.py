import os
import json
import time


class ExperimentInfo:
    LARGE_BRAKE = 0
    SMALL_BRAKE = 1

    def __init__(self):
        self.brake_type = ExperimentInfo.LARGE_BRAKE
        self.conical_annulus_length = 0.0
        self.conical_annulus_od = 0.0
        self.conical_annulus_wall_thickness = 0.0

        self.conical_annulus_length_in = 0.0
        self.conical_annulus_od_in = 0.0
        self.conical_annulus_wall_thickness_in = 0.0

        self.commanded_motor_speed = 0
        self.command_interval = 0.0
        self.time_interval = 0.0
        self.max_torque_command = 0
        self.repeats = 0
        self.brake_type_file_name = ""

        self.commanded_torque_data = []
        self.commanded_motor_data = []
        self.encoder_data = []

        self.start_time = time.time()
        self.initial_encoder_time = None

        self.encoder_start_values = [0.0, 0.0]

    @classmethod
    def get_paths(cls, brake_type):
        if brake_type == ExperimentInfo.LARGE_BRAKE:
            brake_type_file_name = "large_brake"
        else:
            brake_type_file_name = "small_brake"

        return brake_type_file_name

    @classmethod
    def load_from_params(cls, brake_type, length_in, outer_diameter_in, wall_thickness_in,
                         commanded_motor_speed, command_interval, time_interval, repeats):
        in_to_cm = 2.54

        new_obj = cls()
        new_obj.brake_type = brake_type
        new_obj.conical_annulus_length_in = length_in
        new_obj.conical_annulus_od_in = outer_diameter_in
        new_obj.conical_annulus_wall_thickness_in = wall_thickness_in
        new_obj.conical_annulus_length = length_in * in_to_cm
        new_obj.conical_annulus_od = outer_diameter_in * in_to_cm
        new_obj.conical_annulus_wall_thickness = wall_thickness_in * in_to_cm
        new_obj.commanded_motor_speed = commanded_motor_speed
        new_obj.command_interval = command_interval
        new_obj.time_interval = time_interval
        new_obj.max_torque_command = 168 if new_obj.brake_type == ExperimentInfo.SMALL_BRAKE else 174
        new_obj.repeats = repeats

        new_obj.brake_type_file_name = cls.get_paths(brake_type)

        return new_obj

    @classmethod
    def load_from_json(cls, brake_type, conical_annulus_params, experiment_time):
        cm_to_in = 1 / 2.54
        brake_type_file_name = cls.get_paths(brake_type)

        with open(
                "experiments/%s/%s_%s.json" % (conical_annulus_params, brake_type_file_name, experiment_time)) as file:
            params = json.load(file)

        new_obj = cls()
        new_obj.__dict__ = params
        if "initial_encoder_time" not in params:
            new_obj.initial_encoder_time = new_obj.start_time

        if "commanded_motor_data" not in params:
            new_obj.commanded_motor_data = []

        if "conical_annulus_length_in" not in params:
            new_obj.conical_annulus_length_in = round(new_obj.conical_annulus_length * cm_to_in, 4)
        if "conical_annulus_od_in" not in params:
            new_obj.conical_annulus_od_in = round(new_obj.conical_annulus_od * cm_to_in, 4)
        if "conical_annulus_wall_thickness_in" not in params:
            new_obj.conical_annulus_wall_thickness_in = round(new_obj.conical_annulus_wall_thickness * cm_to_in, 4)

        return new_obj

    def record_torque_command(self, timestamp, command):
        self.commanded_torque_data.append((timestamp, command))

    def record_motor_command(self, timestamp, command):
        self.commanded_motor_data.append((timestamp, command))

    def record_encoders(self, timestamp, encoder1_deg, encoder2_deg):
        self.encoder_data.append((timestamp, encoder1_deg, encoder2_deg))

    def record_encoder_start_vals(self, timestamp, encoder1_deg, encoder2_deg):
        self.initial_encoder_time = timestamp
        self.encoder_start_values[0] = encoder1_deg
        self.encoder_start_values[1] = encoder2_deg
        print("initial encoder values @ %s: %s, %s" % (timestamp, encoder1_deg, encoder2_deg))

    def write_experiment_to_file(self):
        conical_annulus_params = "%sx%sx%s" % (
        self.conical_annulus_length_in, self.conical_annulus_od_in, self.conical_annulus_wall_thickness_in)
        path = "experiments/%s/%s_%s.json" % (conical_annulus_params, self.brake_type_file_name, self.start_time)

        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        with open(path, 'w+') as file:
            json.dump(self.__dict__, file)


LENGTH = 2.0
OUTER_DIAMETER = 1.125
WALL_THICKNESS_IN = 0.125
COMMANDED_MOTOR_SPEED = 255

large_brake_experiment = ExperimentInfo.load_from_params(
    ExperimentInfo.LARGE_BRAKE,
    LENGTH, OUTER_DIAMETER, WALL_THICKNESS_IN, COMMANDED_MOTOR_SPEED,
    16, 7, 3
)

small_brake_experiment = ExperimentInfo.load_from_params(
    ExperimentInfo.SMALL_BRAKE,
    LENGTH, OUTER_DIAMETER, WALL_THICKNESS_IN, COMMANDED_MOTOR_SPEED,
    8, 7, 2
)
