import time
import asyncio
from atlasbuggy import Node
from arduino_factory import DeviceFactory, Arduino


class Prototype2bridge(Node):
    def __init__(self, experiment_info, enabled=True, record_to_file=True):
        super(Prototype2bridge, self).__init__(enabled)
        self.factory = DeviceFactory()
        self.prototype2_bridge_arduino = Arduino("prototype2", self.factory)
        self.experiment_info = experiment_info

        self.timestamp_sum = 0.0
        self.num_packets = 0
        self.record_to_file = record_to_file

    async def setup(self):
        # start_packet = self.prototype2_bridge_arduino.start()
        self.prototype2_bridge_arduino.start()

    async def loop(self):
        broadcast_timer = time.time()
        prev_brake_val = 0
        cycle_num = 1
        initial_enc_recorded = False
        if self.record_to_file:
            print("Cycle #%s of %s" % (cycle_num, self.experiment_info.repeats * 2))

        while self.factory.ok():
            packet = self.prototype2_bridge_arduino.read()
            await asyncio.sleep(0.0)

            if packet.name is None:
                self.logger.warning("No packets found!")

            elif packet.name == "enc":
                encoder1_deg = packet.data[0]
                encoder2_deg = packet.data[1]
                self.timestamp_sum += packet.timestamp
                self.num_packets += 1

                if self.record_to_file:
                    if not initial_enc_recorded:
                        # self.experiment_info.record_encoder_start_vals(packet.timestamp, encoder1_deg, encoder2_deg)
                        # initial_enc_recorded = True
                        if packet.timestamp >= 2.0:
                            self.experiment_info.record_encoder_start_vals(packet.timestamp, encoder1_deg, encoder2_deg)
                            initial_enc_recorded = True
                        else:
                            continue

                self.experiment_info.record_encoders(packet.timestamp, encoder1_deg, encoder2_deg)
                await self.broadcast(packet)
                # if time.time() - broadcast_timer > 0.001:
                #     await self.broadcast(packet)
                #     broadcast_timer = time.time()

            elif packet.name == "brake":
                brake_val = packet.data[0]
                self.experiment_info.record_torque_command(packet.timestamp, brake_val)
                print("Torque value '%s' processed" % brake_val)
                if brake_val != prev_brake_val:
                    prev_brake_val = brake_val
                    if brake_val == 0:
                        cycle_num += 1
                        if cycle_num > self.experiment_info.repeats * 2:

                            print("Experiment done")
                            return
                        if self.record_to_file:
                            print("Cycle #%s of %s" % (cycle_num, self.experiment_info.repeats * 2))

            elif packet.name == "motor":
                motor_val = packet.data[0]
                self.experiment_info.record_motor_command(packet.timestamp, motor_val)
                print("Motor speed '%s' processed" % motor_val)

    def generate_experiment(self, command_interval, time_interval, motor_command, repeats, max_torque_command):
        self.command_motor(motor_command)
        self.prototype2_bridge_arduino.write_pause(5)  # wait for twist to settle

        for _ in range(2):  # command in both directions
            for _ in range(repeats):
                self.command_rise(max_torque_command, command_interval, time_interval)

                self.command_brake(max_torque_command)
                self.prototype2_bridge_arduino.write_pause(5)

                self.command_fall(max_torque_command, command_interval, time_interval)

                self.command_brake(0)
                self.prototype2_bridge_arduino.write_pause(5)  # ensure brake dynamics reset

            self.command_motor(-motor_command)

        self.prototype2_bridge_arduino.write_pause(time_interval)
        self.command_motor(0)

    def command_rise(self, max_torque_command, command_interval, time_interval):
        self.command_brake(0)
        brake_command = 0
        for brake_command in range(0, max_torque_command + 1, command_interval):
            self.command_brake(brake_command)
            self.prototype2_bridge_arduino.write_pause(time_interval)

        if brake_command != max_torque_command:
            self.command_brake(max_torque_command)
            self.prototype2_bridge_arduino.write_pause(time_interval)

    def command_fall(self, max_torque_command, command_interval, time_interval):
        self.command_brake(max_torque_command)
        brake_command = 0
        for brake_command in range(max_torque_command, -1, -command_interval):
            self.command_brake(brake_command)
            self.prototype2_bridge_arduino.write_pause(time_interval)

        if brake_command != 0:
            self.command_brake(0)
            self.prototype2_bridge_arduino.write_pause(time_interval)

    def command_brake(self, command):
        self.prototype2_bridge_arduino.write("b" + str(int(command)))

    def command_motor(self, command):
        self.prototype2_bridge_arduino.write("m" + str(int(command)))

    async def teardown(self):
        self.factory.stop_all()
        if self.record_to_file:
            self.experiment_info.write_experiment_to_file()

        print("time fps avg: %0.4f" % (self.timestamp_sum / self.num_packets))
