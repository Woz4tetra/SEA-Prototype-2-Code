from atlasbuggy import Orchestrator, run

from experiment_info import *
from gui.data_plotter import DataPlotter
from prototype2_bridge import Prototype2bridge


class ExperimentOrchestrator(Orchestrator):
    def __init__(self, event_loop, experiment_info):
        super(ExperimentOrchestrator, self).__init__(event_loop)

        self.bridge = Prototype2bridge(experiment_info)
        self.plot = DataPlotter(enabled=True)

        # self.add_nodes(self.bridge)
        self.subscribe(self.bridge, self.plot, self.plot.prototype2_bridge_tag)

    async def setup(self):
        self.bridge.generate_experiment(
            self.bridge.experiment_info.command_interval,
            self.bridge.experiment_info.time_interval,
            self.bridge.experiment_info.commanded_motor_speed,
            self.bridge.experiment_info.repeats,
            self.bridge.experiment_info.max_torque_command,
        )


def main():
    run(ExperimentOrchestrator, large_brake_experiment)
    # run(ExperimentOrchestrator, small_brake_experiment)


main()
