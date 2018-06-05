import numpy as np
import matplotlib.pyplot as plt

# the datasheet for the small brake uses units of oz-in while the large brake datasheet uses lb-in :'(((((


def convert_percent_current_to_amps(array, max_amps):
    array[:, 1] *= max_amps / 100.0


def convert_lbin_to_nm(array):
    array[:, 0] *= lbin_to_nm


def convert_ozin_to_nm(array):
    array[:, 0] *= ozin_to_nm


large_brake_max_current = 0.41
small_brake_max_current = 0.10

large_brake_max_applied_current = 0.31
small_brake_max_applied_current = 0.095

large_brake_min_torque_lbin = 0.3
small_brake_min_torque_ozin = 0.1

ozin_to_nm = 0.0070615518333333
lbin_to_nm = 0.11298482933333

# friction from encoders and ball bearings (oz-in)
# sleeve bushing * 2 = 0.3 * 2, 2 encoder bearings + 2 shaft bearings = 0.05 * 4
no_brake_braking_torque_oz_in = 0.3 * 2 + 0.05 * 4
no_brake_braking_torque_nm = no_brake_braking_torque_oz_in * lbin_to_nm

# large brake ascending torque (lb-in) to percent current
_lba_torque_to_current = np.array([
    [0.031242914796173693, 0.16108047396307512],
    [0.17954996529340406, 9.998081544809882],
    [0.4474988576471368, 14.994994576003965],
    [0.8123332252022237, 19.990791415087426],
    [1.2498316991583227, 24.985751110087936],
    [1.9053224923174614, 29.97819937283956],
    [3.506960504239789, 39.95974732201097],
    [5.423476310566507, 49.93766764682286],
    [7.412656223294237, 59.9147508275518],
    [9.522942980023654, 69.89043876814247],
    [11.609008367952734, 79.8664057567608],
    [13.52552417427945, 89.84432608157269],
    [15.030276711000427, 99.82699022285472],
])
_lba_torque_to_current[:, 0] += large_brake_min_torque_lbin
convert_percent_current_to_amps(_lba_torque_to_current, large_brake_max_current)
convert_lbin_to_nm(_lba_torque_to_current)

# large brake descending torque (lb-in) to percent current
_lbd_torque_to_current = np.array([
    [15.030276711000427, 99.82699022285472],
    [14.03417291908654, 89.83846607299196],
    [12.529420382365565, 79.85580193170996],
    [10.516019100837497, 69.87899779900867],
    [8.526839188109767, 59.90191461827973],
    [6.707208856984401, 49.92287810135721],
    [4.814914419458022, 39.94467872851766],
    [3.116390932334344, 29.96424697145687],
    [1.7085238708147195, 19.98046663806424],
    [0.6398048059046566, 10.154069392268273],
    [0.031242914796173693, 0.16108047396307512],
])
_lbd_torque_to_current[:, 0] += large_brake_min_torque_lbin
convert_percent_current_to_amps(_lbd_torque_to_current, large_brake_max_current)
convert_lbin_to_nm(_lbd_torque_to_current)

# small brake ascending torque (oz-in) to percent current
_sba_torque_to_current = np.array([
    [0.005802707930366857, -0.1160541586073478, ],
    [0.03288201160541693, 4.835589941972923],
    [0.07156673114119894, 9.941972920696326],
    [0.1489361702127665, 15.048355899419732],
    [0.23404255319149048, 20.0],
    [0.36557059961315286, 25.88007736943907],
    [0.4816247582205033, 30.98646034816248],
    [0.8994197292069632, 41.04448742746616],
    [1.1934235976789171, 45.99613152804642],
    [1.4410058027079304, 50.01934235976789],
    [2.0831721470019344, 59.92263056092844],
    [2.7717601547388786, 69.98065764023211],
    [3.4990328820116057, 80.03868471953578],
    [4.0019342359767895, 87.00193423597679],
    [4.23404255319149, 90.09671179883946],
    [5.0, 100.0],
])
_sba_torque_to_current[:, 0] += small_brake_min_torque_ozin
convert_percent_current_to_amps(_sba_torque_to_current, small_brake_max_current)
convert_ozin_to_nm(_sba_torque_to_current)

# small brake descending torque (oz-in) to percent current
_sbd_torque_to_current = np.array([
    [5.0, 100.0],
    [4.9071566731141205, 97.05996131528047],
    [4.752417794970986, 93.81044487427467],
    [4.682785299806577, 92.1083172147002],
    [4.55899419729207, 90.09671179883946],
    [4.087040618955513, 81.89555125725339],
    [3.305609284332689, 69.98065764023211],
    [2.655705996131528, 60.07736943907156],
    [2.0135396518375246, 50.01934235976789],
    [1.402321083172147, 39.96131528046421],
    [0.8607350096711803, 29.90328820116055],
    [0.6750483558994205, 26.034816247582206],
    [0.44294003868471954, 19.845261121856865],
    [0.1798839458413921, 9.941972920696326],
    [0.06382978723404253, 4.835589941972923],
    [-0.005802707930366857, -0.1160541586073478],
])
_sbd_torque_to_current[:, 0] += small_brake_min_torque_ozin
convert_percent_current_to_amps(_sbd_torque_to_current, small_brake_max_current)
convert_ozin_to_nm(_sbd_torque_to_current)

# large brake current (amps) to 0...255
_lb_current_to_bytes = np.array([
    [0.01, 0],
    [0.03, 16],
    [0.05, 16 * 2],
    [0.07, 16 * 3],
    [0.09, 16 * 4],
    [0.11, 16 * 5],
    [0.131, 16 * 6],
    [0.151, 16 * 7],
    [0.172, 16 * 8],
    [0.193, 16 * 9],
    [0.213, 16 * 10],
    [0.2345, 16 * 11],
    [0.253, 16 * 12],
    [0.278, 16 * 13],
    [0.295, 16 * 14],
    [0.297, 16 * 15],
    [0.303, 255],
])

# small brake current (amps) to 0...255
_sb_current_to_bytes = np.array([
    [0.004, 0],
    [0.014, 16],
    [0.024, 16 * 2],
    [0.033, 16 * 3],
    [0.043, 16 * 4],
    [0.052, 16 * 5],
    [0.062, 16 * 6],
    [0.071, 16 * 7],
    [0.081, 16 * 8],
    [0.090, 16 * 9],
    [0.095, 16 * 10],
    [0.095, 16 * 11],
    [0.095, 16 * 12],
    [0.095, 16 * 13],
    [0.095, 16 * 14],
    [0.095, 16 * 15],
    [0.095, 255],
])


def get_brake_lookup_table(torque_to_current, current_to_bytes, ascending=True, plot_results=False):
    if not ascending:
        torque_to_current = np.flip(torque_to_current, 0)
    byte_range = np.array(range(0, 256))

    torque_to_current[:, 0] += no_brake_braking_torque_nm
    interp_torque = np.interp(current_to_bytes[:, 0], torque_to_current[:, 1], torque_to_current[:, 0])

    lookup_table = np.interp(byte_range, current_to_bytes[:, 1], interp_torque)

    if plot_results:
        plt.figure(1)
        plt.plot(torque_to_current[:, 1], torque_to_current[:, 0], '.-', label="current to torque")
        plt.plot(current_to_bytes[:, 0], interp_torque, 'x', label="interp current to torque")
        plt.legend()

        plt.figure(2)
        plt.title("bytes to torque")
        plt.plot(byte_range, lookup_table)

    return lookup_table.tolist()


def write_to_file(file_name, lookup_table):
    with open(file_name, 'w+') as file:
        for row in lookup_table:
            file.write("%s\n" % str(row))


write_to_file("lookup_tables/large_brake_ascending.csv",
              get_brake_lookup_table(_lba_torque_to_current, _lb_current_to_bytes))
write_to_file("lookup_tables/large_brake_descending.csv",
              get_brake_lookup_table(_lbd_torque_to_current, _lb_current_to_bytes, False))

write_to_file("lookup_tables/small_brake_ascending.csv",
              get_brake_lookup_table(_sba_torque_to_current, _sb_current_to_bytes))
write_to_file("lookup_tables/small_brake_descending.csv",
              get_brake_lookup_table(_sbd_torque_to_current, _sb_current_to_bytes, False))

plt.show()
