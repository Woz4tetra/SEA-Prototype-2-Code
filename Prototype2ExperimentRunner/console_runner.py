from atlasbuggy import Orchestrator, run

from experiment_info import *
from gui.data_plotter import DataPlotter
from prototype2_bridge import Prototype2bridge
from gui.control_ui import TkinterGUI


class ConsoleOrchestrator(Orchestrator):
    def __init__(self, event_loop, experiment_info):
        super(ConsoleOrchestrator, self).__init__(event_loop)

        self.bridge = Prototype2bridge(experiment_info, record_to_file=False)
        self.plot = DataPlotter()
        self.gui = TkinterGUI()

        self.subscribe(self.bridge, self.plot, self.plot.prototype2_bridge_tag)
        self.subscribe(self.bridge, self.gui, self.gui.prototype2_bridge_tag)


def main():
    run(ConsoleOrchestrator, small_brake_experiment)


main()
