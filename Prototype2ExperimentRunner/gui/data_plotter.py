import asyncio
from threading import Event

from atlasbuggy import Node


class DataPlotter(Node):
    def __init__(self, enabled=True):
        super(DataPlotter, self).__init__(enabled)

        self.pause_time = 1 / 30
        self.exit_event = Event()
        self.plot_paused = False

        self.prototype2_bridge_tag = "prototype2_bridge"
        self.prototype2_bridge_sub = self.define_subscription(self.prototype2_bridge_tag)
        self.prototype2_bridge_queue = None

        self.diff_plot_time_window = 120.0
        self.enc_plot_time_window = 5.0

        self.encoder_diff_timestamps = []
        self.encoder_diff_data = []

        self.encoder_timestamps = []
        self.encoder_data_1 = []
        self.encoder_data_2 = []

        self.initial_val_enc_1 = None
        self.initial_val_enc_2 = None

        self.gear_ratio = 32.0 / 48.0

        self.plt = None
        if self.enabled:
            self.enable_matplotlib()
            self.fig = self.plt.figure(1)
            self.fig.canvas.mpl_connect('key_press_event', self.press)
            self.fig.canvas.mpl_connect('close_event', lambda event: self.exit_event.set())

    def enable_matplotlib(self):
        from matplotlib import pyplot as plt
        self.plt = plt

    def take(self):
        self.prototype2_bridge_queue = self.prototype2_bridge_sub.get_queue()

    async def setup(self):
        # if self.is_subscribed(self.bno055_tag):
        #     self.bno_plot = self.fig.add_subplot(2, 1, 1)
        #     self.bno_data_line = self.bno_plot.plot([], [], '-', label="angle")[0]
        #
        #     self.speed_plot = self.fig.add_subplot(2, 1, 2)
        #
        #     self.bno_plot.legend(fontsize="x-small", shadow="True", loc=0)
        # else:
        self.diff_plot = self.fig.add_subplot(2, 1, 1)
        self.encoder_plot = self.fig.add_subplot(2, 1, 2)
        # self.encoder_plot = self.fig.add_subplot(1, 1, 1)

        self.diff_line = self.diff_plot.plot([], [], '-', label="enc diff")[0]
        self.encoder_line_1 = self.encoder_plot.plot([], [], '.-', label="enc1")[0]
        self.encoder_line_2 = self.encoder_plot.plot([], [], '.-', label="enc2")[0]
        self.encoder_plot.legend(fontsize="x-small", shadow="True", loc=0)

        self.plt.ion()
        self.plt.show(block=False)

    async def loop(self):
        while True:
            if self.exit_event.is_set():
                return

            if self.plot_paused:
                await self.draw()
                continue

            await self.get_encoder_data()
            if len(self.encoder_diff_timestamps) == 0:
                await self.draw()
                continue

            while self.encoder_diff_timestamps[-1] - self.encoder_diff_timestamps[0] > self.diff_plot_time_window:
                self.encoder_diff_timestamps.pop(0)
                self.encoder_diff_data.pop(0)

            while self.encoder_timestamps[-1] - self.encoder_timestamps[0] > self.enc_plot_time_window:
                self.encoder_timestamps.pop(0)
                self.encoder_data_1.pop(0)
                self.encoder_data_2.pop(0)

            self.plot_data()
            await self.draw()

    def plot_data(self):
        self.encoder_line_1.set_xdata(self.encoder_timestamps)
        self.encoder_line_1.set_ydata(self.encoder_data_1)

        self.encoder_line_2.set_xdata(self.encoder_timestamps)
        self.encoder_line_2.set_ydata(self.encoder_data_2)

        self.diff_line.set_xdata(self.encoder_diff_timestamps)
        self.diff_line.set_ydata(self.encoder_diff_data)

        self.encoder_plot.relim()
        self.encoder_plot.autoscale_view()

        self.diff_plot.relim()
        self.diff_plot.autoscale_view()

    async def get_encoder_data(self):
        while not self.prototype2_bridge_queue.empty():
            # message = await asyncio.wait_for(self.prototype2_bridge_queue.get(), timeout=1)
            message = self.prototype2_bridge_queue.get_nowait()

            if self.initial_val_enc_1 is None:
                self.initial_val_enc_1 = message.data[0]

            if self.initial_val_enc_2 is None:
                self.initial_val_enc_2 = message.data[1]

            enc1_angle = (message.data[0] - self.initial_val_enc_1) * self.gear_ratio
            enc2_angle = (message.data[1] - self.initial_val_enc_2) * self.gear_ratio

            # enc1_angle = message.data[0] * self.gear_ratio
            # enc2_angle = message.data[1] * self.gear_ratio

            self.encoder_timestamps.append(message.timestamp)
            self.encoder_diff_timestamps.append(message.timestamp)
            self.encoder_diff_data.append(enc1_angle - enc2_angle)
            self.encoder_data_1.append(message.data[2])
            self.encoder_data_2.append(message.data[3])

    def press(self, event):
        """matplotlib key press event. Close all figures when q is pressed"""
        if event.key == "q":
            self.exit_event.set()
        if event.key == " ":
            self.plot_paused = not self.plot_paused
            print("Plot is paused:", self.plot_paused)

    async def draw(self):
        self.fig.canvas.draw()
        self.plt.pause(self.pause_time)
        await asyncio.sleep(self.pause_time)

    async def teardown(self):
        self.plt.close("all")
