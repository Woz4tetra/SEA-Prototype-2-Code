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


def save_fig(title, brake_type_file_name, experiment_time):
    path = "figures/%s_%s_%s.png" % (title, brake_type_file_name, experiment_time)
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


def get_lookup_tables(experiment_params):
    ascending_lookup_filename = "lookup_tables/%s_ascending.csv" % str(experiment_params.brake_type_file_name)
    with open(ascending_lookup_filename, 'r') as file:
        data = file.read().splitlines()
        ascending_command_to_torque = list(map(float, data))

    descending_lookup_filename = "lookup_tables/%s_descending.csv" % str(experiment_params.brake_type_file_name)
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

    commanded_torque_nm_data = np.array(commanded_torque_nm_data)

    return torque_timestamps, commanded_torque_nm_data


def format_encoder_data(experiment_info, gear_ratio):
    encoder_data = np.array(experiment_info.encoder_data)
    encoder_timestamps = encoder_data[:, 0]

    encoder_data[:, 1] -= encoder_data[0, 1]
    encoder_data[:, 2] -= encoder_data[0, 2]

    encoder_data[:, 1] *= gear_ratio
    encoder_data[:, 2] *= gear_ratio

    # remove random jumps (software error)
    encoder_delta = encoder_data[:, 1] - encoder_data[:, 2]
    avg_diff = np.average(encoder_delta)
    std_dev = np.std(encoder_delta)
    outlier_indices = np.where(np.abs(encoder_delta - avg_diff) > std_dev * 2)
    encoder_delta = np.delete(encoder_delta, outlier_indices)
    encoder_timestamps = np.delete(encoder_timestamps, outlier_indices)

    # # remove instances of the motor shutting off during stall
    # stall_indices = np.where(np.diff(encoder_delta) > 4)[0]
    # for search_index in range(0, len(stall_indices) - 1, 2):
    #     lower_stall_index = stall_indices[search_index]
    #     upper_stall_index = stall_indices[search_index + 1]
    #
    #     deletion_indices = np.arange(lower_stall_index, upper_stall_index, 1)
    #     encoder_delta = np.delete(encoder_delta, deletion_indices)
    #     encoder_timestamps = np.delete(encoder_timestamps, deletion_indices)

    return encoder_delta, encoder_timestamps


def hysteresis_fn(x, a, b, c):
    return a * (x + b) ** 3 + c
    # return a * np.tan(b * x + c)


def analyze_experiment(experiment_params, experiment_time, plot_results=True):
    gear_ratio = 32.0 / 48.0
    ascending_command_to_torque, descending_command_to_torque = get_lookup_tables(experiment_params)

    experiment_info = ExperimentInfo.load_from_json(experiment_params.brake_type, experiment_time)

    settling_time = experiment_info.time_interval / 3
    torque_timestamps, commanded_torque_nm_data = format_torque_data(experiment_info, ascending_command_to_torque,
                                                                     descending_command_to_torque, settling_time)

    encoder_delta, encoder_timestamps = format_encoder_data(experiment_info, gear_ratio)
    # print(encoder_timestamps[np.where(encoder_delta > 60)][0])
    encoder_delta_smoothed = savitzky_golay(encoder_delta, 401, 5)
    encoder_interp = np.interp(torque_timestamps, encoder_timestamps, encoder_delta_smoothed)

    polynomial = np.polyfit(encoder_interp, commanded_torque_nm_data, 1)
    linear_regression_fn = np.poly1d(polynomial)
    encoder_lin_reg = linear_regression_fn(encoder_interp)

    # popt, pcov = curve_fit(hysteresis_fn, encoder_interp, commanded_torque_nm_data)

    if plot_results:
        new_fig()
        plt.plot(torque_timestamps, commanded_torque_nm_data, '.-', label="torque data")

        title = "Applied torque vs. time"
        plt.title(title)
        plt.xlabel("time (s)")
        plt.ylabel("applied torque (N•m)")
        save_fig(title, experiment_info.brake_type_file_name, experiment_time)

        new_fig()
        plt.plot(encoder_timestamps, encoder_delta, '-.', label="encoder delta", markersize=0.5)
        plt.plot(encoder_timestamps, encoder_delta_smoothed, linewidth=0.5, label="smoothed")
        plt.plot(torque_timestamps, encoder_interp, 'x', markersize=5, color='red', label="interpolated")

        title = "Encoder data"
        plt.title(title)
        plt.xlabel("time (s)")
        plt.ylabel("encoder delta (degrees)")
        save_fig(title, experiment_info.brake_type_file_name, experiment_time)

        new_fig()
        plt.plot(encoder_interp, commanded_torque_nm_data, 'x', label="data")
        plt.plot(encoder_interp, encoder_lin_reg,
                 label='m=%0.4f, b=%0.4f' % (polynomial[0], polynomial[1]))
        # plt.plot(encoder_interp, hysteresis_fn(encoder_interp, *popt), 'r-',
        #          label='fit: a=%5.3f, b=%5.3f, c=%5.3f' % tuple(popt))
        plt.legend()

        title = "Hysteresis of conical annulus"
        plt.title(title)
        plt.xlabel("encoder delta (degrees)")
        plt.ylabel("applied torque (N•m)")
        save_fig(title, experiment_info.brake_type_file_name, experiment_time)

        plt.show()

    return commanded_torque_nm_data, encoder_interp, encoder_lin_reg


def plot_combined_experiments(torques, enc_interps, enc_lin_regs):
    assert len(torques) == len(enc_interps) == len(enc_lin_regs)
    for index in range(len(torques)):
        plt.plot(enc_interps[index], torques[index], 'x', label="interp #%s" % (index + 1))
        plt.plot(enc_interps[index], enc_lin_regs[index], label="regression #%s" % (index + 1))

    plt.legend()
    plt.show()


# torque_large, enc_interp_large, enc_lin_large = analyze_experiment(large_brake_experiment, 1528141782.467071, plot_results=True)
torque_small, enc_interp_small, enc_lin_small = analyze_experiment(small_brake_experiment, 1528165346.742316, plot_results=True)
# plot_combined_experiments(
#     [torque_large, torque_small],
#     [enc_interp_large, enc_interp_small],
#     [enc_lin_large, enc_lin_small]
# )
