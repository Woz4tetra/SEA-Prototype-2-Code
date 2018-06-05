import math
import asyncio
from experiment_info import *
from data_plotter import DataPlotter

from atlasbuggy import Orchestrator, Node, run
from arduino_factory import DeviceFactory, Arduino


class Prototype2bridge(Node):
    def __init__(self, experiment_info, enabled=True):
        super(Prototype2bridge, self).__init__(enabled)
        self.factory = DeviceFactory()
        self.prototype2_bridge_arduino = Arduino("prototype2", self.factory)
        self.experiment_info = experiment_info

    async def setup(self):
        start_packet = self.prototype2_bridge_arduino.start()
        self.experiment_info.record_encoder_start_vals(*start_packet.data)
        self.generate_experiment(
            self.experiment_info.command_interval,
            self.experiment_info.time_interval,
            self.experiment_info.commanded_motor_speed,
            self.experiment_info.repeats,
            self.experiment_info.max_torque_command,
        )

    async def loop(self):
        broadcast_timer = time.time()

        while self.factory.ok():
            packet = self.prototype2_bridge_arduino.read()
            if packet.name is None:
                self.logger.warning("No packets found!")

            elif packet.name == "enc":
                encoder1_deg = packet.data[0]
                encoder2_deg = packet.data[1]
                self.experiment_info.record_encoders(packet.timestamp, encoder1_deg, encoder2_deg)
                if time.time() - broadcast_timer > 0.01:
                    await self.broadcast(packet)
                    broadcast_timer = time.time()

            elif packet.name == "brake":
                brake_val = packet.data[0]
                self.experiment_info.record_torque_command(packet.timestamp, brake_val)
                print("Torque value '%s' processed" % brake_val)

            await asyncio.sleep(0.0)

    def generate_experiment(self, command_interval, time_interval, motor_command, repeats, max_torque_command):
        self.command_motor(motor_command)

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
        self.prototype2_bridge_arduino.write("b" + str(command))

    def command_motor(self, command):
        self.prototype2_bridge_arduino.write("m" + str(command))

    async def teardown(self):
        self.factory.stop_all()
        self.experiment_info.write_experiment_to_file()


class ExperimentOrchestrator(Orchestrator):
    def __init__(self, event_loop, experiment_info):
        super(ExperimentOrchestrator, self).__init__(event_loop)

        self.bridge = Prototype2bridge(experiment_info)
        self.plot = DataPlotter()

        self.subscribe(self.bridge, self.plot, self.plot.prototype2_bridge_tag)


def main():
    run(ExperimentOrchestrator, small_brake_experiment)


main()
