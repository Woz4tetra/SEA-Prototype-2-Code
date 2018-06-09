import os
import math
# import scipy
import numpy as np
import matplotlib.pyplot as plt
# from scipy.interpolate import CubicSpline
from scipy.optimize import curve_fit

from experiment_info import *

current_fig_num = 0


def press(event):
    """matplotlib key press event. Close all figures when q is pressed"""
    if event.key == "q":
        plt.close("all")


def new_fig(fig_num=None):
    """Create a new figure"""

    global current_fig_num, current_fig
    if fig_num is None:
        current_fig_num += 1
    else:
        current_fig_num = fig_num
    fig = plt.figure(current_fig_num)
    fig.canvas.mpl_connect('key_press_event', press)
    current_fig = fig

    return fig


def mkdir(path, is_file=True):
    if is_file:
        path = os.path.split(path)[0]  # remove the file part of the path

    if not os.path.isdir(path):
        os.makedirs(path)


def save_fig(title, brake_type_file_name, conical_annulus_params, experiment_time):
    path = "figures/%s/%s_%s_%s.png" % (conical_annulus_params, title, brake_type_file_name, experiment_time)
    mkdir(path)
    print("saving to '%s'" % path)
    plt.savefig(path, dpi=200)


def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except ValueError:
        raise ValueError("window_size and order have to be of type int")

    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")

    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")

    order_range = range(order + 1)
    half_window = (window_size - 1) // 2
    # precompute coefficients
    b = np.mat([[k ** i for i in order_range] for k in range(-half_window, half_window + 1)])
    m = np.linalg.pinv(b).A[deriv] * rate ** deriv * math.factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs(y[1:half_window + 1][::-1] - y[0])
    lastvals = y[-1] + np.abs(y[-half_window - 1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve(m[::-1], y, mode='valid')


def get_lookup_tables(brake_type):
    brake_type_file_name = ExperimentInfo.get_paths(brake_type)
    ascending_lookup_filename = "lookup_tables/%s_ascending.csv" % str(brake_type_file_name)
    with open(ascending_lookup_filename, 'r') as file:
        data = file.read().splitlines()
        ascending_command_to_torque = list(map(float, data))

    descending_lookup_filename = "lookup_tables/%s_descending.csv" % str(brake_type_file_name)
    with open(descending_lookup_filename, 'r') as file:
        data = file.read().splitlines()
        descending_command_to_torque = list(map(float, data))

    return ascending_command_to_torque, descending_command_to_torque


def format_torque_data(experiment_info, ascending_command_to_torque, descending_command_to_torque, settling_time):
    commanded_torque_data = np.array(experiment_info.commanded_torque_data)
    torque_timestamps = commanded_torque_data[:, 0] + settling_time  # account for settling time
    torque_commands = commanded_torque_data[:, 1]

    # remove repeating commands
    repeating_indices = np.where(np.diff(torque_commands) == 0)
    torque_timestamps = np.delete(torque_timestamps, repeating_indices)
    torque_commands = np.delete(torque_commands, repeating_indices)

    # find all zero peaks
    all_indices_of_zero_torque = np.where(torque_commands == 0)[0]
    prev_index = all_indices_of_zero_torque[0]
    zero_torque_valleys = [prev_index]
    for index in all_indices_of_zero_torque:
        if index - prev_index > 1:
            zero_torque_valleys.append(index)
        prev_index = index

    # where the repeat occurs is when the motor changes directions
    direction_transition = zero_torque_valleys[experiment_info.repeats]

    # find all rising and falling transitions
    rising_indices = np.where(np.diff(torque_commands) > 0)[0]

    # convert command to nm according to direction and whether the torque is rising or falling
    commanded_torque_nm_data = []
    for torque_index in range(len(torque_commands)):
        commanded_torque = torque_commands[torque_index]
        if torque_index in rising_indices:
            commanded_torque_nm_data.append(ascending_command_to_torque[int(commanded_torque)])
        else:
            commanded_torque_nm_data.append(descending_command_to_torque[int(commanded_torque)])

        if torque_index >= direction_transition:
            commanded_torque_nm_data[-1] *= -1

        if experiment_info.commanded_motor_speed < 0:
            commanded_torque_nm_data[-1] *= -1

    commanded_torque_nm_data = np.array(commanded_torque_nm_data)

    if len(experiment_info.commanded_motor_data) > 0:
        selected_index = 0
        for index in range(0, len(experiment_info.commanded_motor_data) - 1):
            current_motor_command = experiment_info.commanded_motor_data[index][1]
            prev_motor_command = experiment_info.commanded_motor_data[index + 1][1]
            if current_motor_command != prev_motor_command:
                selected_index = index + 1
                break

        direction_change_timestamp = experiment_info.commanded_motor_data[selected_index][0]
    else:
        direction_change_timestamp = 0.0

    return torque_timestamps, commanded_torque_nm_data, direction_change_timestamp


def format_encoder_data(experiment_info, direction_change_timestamp, gear_ratio):
    encoder_data = np.array(experiment_info.encoder_data)
    encoder_timestamps = encoder_data[:, 0]
    encoder_1_ticks = encoder_data[:, 1]
    encoder_2_ticks = encoder_data[:, 2]

    # direction_change_index = 0
    encoder_1_ticks -= encoder_1_ticks[0]
    encoder_2_ticks -= encoder_2_ticks[0]

    encoder_1_ticks *= gear_ratio
    encoder_2_ticks *= gear_ratio

    encoder_delta = encoder_1_ticks - encoder_2_ticks

    # remove random jumps (software error)
    avg_diff = np.average(encoder_delta)
    std_dev = np.std(encoder_delta)
    outlier_indices = np.where(np.abs(encoder_delta - avg_diff) > std_dev * 6)[0]

    encoder_delta_filtered = np.delete(encoder_delta, outlier_indices)
    encoder_timestamps_filtered = np.delete(encoder_timestamps, outlier_indices)

    # # remove instances of the motor shutting off during stall
    # stall_indices = np.where(np.diff(encoder_delta) > 4)[0]
    # for search_index in range(0, len(stall_indices) - 1, 2):
    #     lower_stall_index = stall_indices[search_index]
    #     upper_stall_index = stall_indices[search_index + 1]
    #
    #     deletion_indices = np.arange(lower_stall_index, upper_stall_index, 1)
    #     encoder_delta = np.delete(encoder_delta, deletion_indices)
    #     encoder_timestamps = np.delete(encoder_timestamps, deletion_indices)

    encoder_delta_smoothed = savitzky_golay(encoder_delta_filtered, 501, 5)

    if direction_change_timestamp > 0.0:
        direction_change_timestamp += 0.5  # add some time, wait for motor to actually change directions
        direction_change_index = np.argmin(np.abs(encoder_timestamps - direction_change_timestamp))

        # cancel out any gear backlash
        encoder_delta_smoothed[:direction_change_index] -= encoder_delta_smoothed[0]
        encoder_delta_smoothed[direction_change_index:] -= encoder_delta_smoothed[direction_change_index]

    return encoder_delta, encoder_timestamps, encoder_delta_smoothed, encoder_delta_filtered, encoder_timestamps_filtered


def hysteresis_fn(x, a, b, c):
    return a * (x + b) ** 3 + c
    # return a * np.tan(b * x + c)


class ExperimentResults:
    def __init__(self):
        self.torque_input = None
        self.encoder_output = None
        self.encoder_linear_regression = None
        self.lin_reg_coeffs = None


def analyze_experiment(brake_type, conical_annulus_params, experiment_time):
    gear_ratio = 32.0 / 48.0
    results = ExperimentResults()
    ascending_command_to_torque, descending_command_to_torque = get_lookup_tables(brake_type)

    experiment_info = ExperimentInfo.load_from_json(brake_type, conical_annulus_params, experiment_time)

    settling_time = experiment_info.time_interval / 3
    torque_timestamps, commanded_torque_nm_data, direction_change_timestamp = \
        format_torque_data(experiment_info, ascending_command_to_torque,
                           descending_command_to_torque, settling_time)

    format_enc_results = format_encoder_data(experiment_info, direction_change_timestamp, gear_ratio)
    # encoder_delta = results[0]
    # encoder_timestamps = results[1]
    encoder_delta_smoothed = format_enc_results[2]
    encoder_delta_filtered = format_enc_results[3]
    encoder_timestamps_filtered = format_enc_results[4]

    encoder_interp = np.interp(torque_timestamps, encoder_timestamps_filtered, encoder_delta_smoothed)

    polynomial = np.polyfit(encoder_interp, commanded_torque_nm_data, 1)
    linear_regression_fn = np.poly1d(polynomial)
    encoder_lin_reg = linear_regression_fn(encoder_interp)

    # popt, pcov = curve_fit(hysteresis_fn, encoder_interp, commanded_torque_nm_data)

    if PLOT_RESULTS:
        new_fig()
        plt.plot(torque_timestamps, commanded_torque_nm_data, '.-', label="torque data")

        title = "Applied torque vs. time"
        plt.title(title)
        plt.xlabel("time (s)")
        plt.ylabel("applied torque (N•m)")
        if SAVE_FIGS:
            save_fig(title, experiment_info.brake_type_file_name, conical_annulus_params, experiment_time)

        new_fig()
        # plt.plot(encoder_timestamps, encoder_delta, '-.', label="encoder delta", markersize=0.5)
        plt.plot(encoder_timestamps_filtered, encoder_delta_filtered, '-.', label="encoder delta", markersize=0.5)
        plt.plot(encoder_timestamps_filtered, encoder_delta_smoothed, linewidth=0.5, label="smoothed")
        plt.plot(torque_timestamps, encoder_interp, 'x', markersize=5, color='red', label="interpolated")
        plt.legend()

        title = "Encoder data"
        plt.title(title)
        plt.xlabel("time (s)")
        plt.ylabel("encoder delta (degrees)")
        if SAVE_FIGS:
            save_fig(title, experiment_info.brake_type_file_name, conical_annulus_params, experiment_time)

        new_fig()
        plt.plot(encoder_interp, commanded_torque_nm_data, 'x', label="data")
        plt.plot(encoder_interp, encoder_lin_reg,
                 label='m=%0.4f, b=%0.4f' % (polynomial[0], polynomial[1]))
        # plt.plot(encoder_interp, hysteresis_fn(encoder_interp, *popt), 'r-',
        #          label='fit: a=%5.3f, b=%5.3f, c=%5.3f' % tuple(popt))
        plt.plot(0, 0, '+', markersize=15)
        plt.legend()

        title = "Hysteresis of conical annulus"
        plt.title(title)
        plt.xlabel("encoder delta (degrees)")
        plt.ylabel("applied torque (N•m)")
        if SAVE_FIGS:
            save_fig(title, experiment_info.brake_type_file_name, conical_annulus_params, experiment_time)

        plt.show()

    results.torque_input = commanded_torque_nm_data
    results.encoder_output = encoder_interp
    results.encoder_linear_regression = encoder_lin_reg
    results.lin_reg_coeffs = polynomial

    return results


def plot_combined_experiments(*results):
    for index in range(len(results)):
        plt.plot(results[index].encoder_output, results[index].torque_input, 'x', label="interp #%s" % (index + 1))
        plt.plot(results[index].encoder_output, results[index].encoder_linear_regression,
                 label='m=%0.4f, b=%0.4f' % (results[index].lin_reg_coeffs[0], results[index].lin_reg_coeffs[1]))

    plt.plot(0, 0, '+', markersize=25)
    plt.legend()
    plt.show()


SAVE_FIGS = False
PLOT_RESULTS = False

results_large_1 = analyze_experiment(ExperimentInfo.LARGE_BRAKE, "1.0x0.75x0.125", 1528141782.467071)
results_small_1 = analyze_experiment(ExperimentInfo.SMALL_BRAKE, "1.0x0.75x0.125", 1528165346.742316)
# plot_combined_experiments(results_large_1, results_small_1)

results_large_2 = analyze_experiment(ExperimentInfo.LARGE_BRAKE, "1.5x0.75x0.125", 1528522129.6387455)
results_small_2 = analyze_experiment(ExperimentInfo.SMALL_BRAKE, "1.5x0.75x0.125", 1528484673.3223443)
# plot_combined_experiments(results_large_2, results_small_2)

# plot_combined_experiments(results_large_1, results_large_2)
plot_combined_experiments(results_small_1, results_small_2)
