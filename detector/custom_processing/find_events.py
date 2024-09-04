import math
from datetime import timedelta, datetime

import numpy as np
from scipy import signal

import detector.custom_processing.consts as consts


# Auxiliary function
def l_calc(cl1, sl1, cl2, sl2, long1, long2):
    rad = 6363418 # Earth radius in meters
    delta12 = long2 - long1
    cdelta12 = math.cos(delta12)
    sdelta12 = math.sin(delta12)

    y12 = math.sqrt(math.pow(cl2 * sdelta12, 2) + math.pow(cl1 * sl2 - sl1 * cl2 * cdelta12, 2))
    x12 = sl1 * sl2 + cl1 * cl2 * cdelta12
    ad12 = math.atan2(y12, x12)
    l_2 = ad12 * rad
    return l_2, cdelta12, sdelta12


# Main 'Calculate azimuth' function
def angles_calc(lat1, long1, t1, lat2, long2, t2, lat3, long3, t3):

    (t1, lat1, long1), (t3, lat3, long3), (t2, lat2, long2) = \
        sorted(((t1, lat1, long1), (t2, lat2, long2), (t3, lat3, long3)))

    if t1 == t2:
        t1 -= timedelta(seconds=0.0001)
    if t3 == t2:
        t3 += timedelta(seconds=0.0001)

    lat1, lat2, lat3, long1, long2, long3 = \
        [lat_lon * math.pi / 180. for lat_lon in (lat1, lat2, lat3, long1, long2, long3)]

    (cl1, sl1), (cl2, sl2), (cl3, sl3) = [(math.cos(lat), math.sin(lat)) for lat in (lat1, lat2, lat3)]

    l_2, _, _ = l_calc(cl1, sl1, cl2, sl2, long1, long2)
    l_3, _, _ = l_calc(cl1, sl1, cl3, sl3, long1, long3)
    l_1, cdelta23, sdelta23 = l_calc(cl2, sl2, cl3, sl3, long2, long3)

    # Calculate alpha1
    cos_omega = (l_3 ** 2 - l_2 ** 2 - l_1 ** 2) / (-2 * l_1 * l_2)
    omega = math.acos(cos_omega)
    tau_1 = t2 - t3
    tau_2 = t2 - t1

    tan_b1 = ((tau_2 * l_1) / (tau_1 * l_2 * math.sin(omega)) - (math.tan(omega)) ** (-1))
    b1 = math.atan(tan_b1) * 180 / math.pi

    # Azimuth 2-3
    x = (cl2 * sl3) - (sl2 * cl3 * cdelta23)
    y = sdelta23 * cl3
    z = math.degrees(math.atan(-y / x))

    if x < 0:
        z = z + 180.

    z2 = (z + 180.) % 360. - 180.
    z2 = - math.radians(z2)
    angle23 = (z2 - ((2 * math.pi) * math.floor((z2 / (2 * math.pi)))))
    azimut23 = (angle23 * 180) / math.pi

    # Azimuth 2-1
    delta21 = long1 - long2
    cdelta21 = math.cos(delta21)
    sdelta21 = math.sin(delta21)
    x = (cl2 * sl1) - (sl2 * cl1 * cdelta21)
    y = sdelta21 * cl1
    z = math.degrees(math.atan(-y / x))

    if x < 0:
        z = z + 180.

    z21 = (z + 180.) % 360. - 180.
    z21 = - math.radians(z21)
    angle21 = (z21 - ((2 * math.pi) * math.floor((z21 / (2 * math.pi)))))
    azimut21 = (angle21 * 180) / math.pi

    if (azimut23 - azimut21) > 0:
        if (azimut23 - azimut21) < 180:
            azimut2S = azimut23 - b1
        else:
            azimut2S = azimut23 + b1
    else:
        if (azimut21 - azimut23) < 180:
            azimut2S = azimut23 + b1
        else:
            azimut2S = azimut23 - b1

    azimut2S = (azimut2S + 360) % 360
    return b1, azimut2S


#### Auxiliary functions
## Calculate moving_avg from array, return array of the same size
def moving_avg(x, n):
    cumsum = np.cumsum(x, dtype=float)
    out = (cumsum[n:] - cumsum[:-n]) / float(n)
    out_start = np.full((n), out[0])
    return np.concatenate((out_start, out))


#### Auxiliary functions
## Calculate shifted_moving_avg from array, return array of the same size
def shifted_moving_avg(x, n, shift):
    cumsum = np.cumsum(x, dtype=float)
    out = (cumsum[n:] - cumsum[:-n]) / float(n)
    out_start = np.full((n+shift), out[0])
    return np.concatenate((out_start, out[:-shift]))


## Calculate delays t12=t2-t1 and t13=t3-t1 using crosscorrelation method
def delay_by_crosscorrelation(event):
    cc12=signal.correlate(event['data']['ch1'], event['data']['ch2'], mode='full', method='auto')
    cc13=signal.correlate(event['data']['ch1'], event['data']['ch3'], mode='full', method='auto')
    t12=cc12.argmax()-event['data']['ch1'].size
    t13=cc13.argmax()-event['data']['ch1'].size
    return (timedelta(seconds=t12/1000), timedelta(seconds=t13/1000)) # divide by 1000 to get seconds


#### Main 'find peak triplets' function
def find_peak_triplets(dd, data_buf_duration: int):
    ''' dd is a dict:
        'dt': numpy array of datetime stamps
        'ch1', 'ch2', 'ch3': numpy array of signal in specific channel
    '''

    peaks = []
    for i in range(consts.NUMBER_OF_CHANNELS):
        V_channel = dd['ch' + str(i + 1)]

        height_channel = shifted_moving_avg(abs(V_channel), consts.WINDOW_MOVING_AVG, consts.SHIFT_MOVING_AVG)

        peaks.append(signal.find_peaks(V_channel, height=height_channel * consts.SIGNAL_TO_AVG_RATE, distance=1000))

    # Find close peaks in all three channels
    MAX_DELTA = 500  # in microseconds
    peak_triplets = []
    for p0 in peaks[0][0].tolist():
        peaks2 = peaks[1][0][abs(peaks[1][0] - p0) < MAX_DELTA]
        peaks3 = peaks[2][0][abs(peaks[2][0] - p0) < MAX_DELTA]
        if peaks2.size > 0 and peaks3.size > 0:
            peak_triplets.append((p0, peaks2[0], peaks3[0]))

    result = []
    for pt in peak_triplets:
        if max(pt) < data_buf_duration - MAX_DELTA:  # Do not add events that has just appeared in the buffer
            result.append({'t1': dd['dt'][pt[0]], 't2': dd['dt'][pt[1]], 't3': dd['dt'][pt[2]], 'data': dd})

    return result


def find_events(data_dict, data_buf_duration: int):
    dd = {}
    # Add list of datetimes as numpy array
    dd['dt'] = np.arange(data_dict['t0'], data_dict['t0'] + timedelta(milliseconds=data_buf_duration),
                         timedelta(milliseconds=1)).astype(datetime)

    ## Shift signal average to zero for each channel
    for i in range(3):
        dd['ch' + str(i + 1)] = data_dict['ch' + str(i + 1)] - data_dict['ch' + str(i + 1)].mean()

    ## Find peaks approach
    events = find_peak_triplets(dd, data_buf_duration)

    for e in events:
        e['azimuth1'] = angles_calc(consts.LAT1, consts.LON1, e['t1'], consts.LAT2, consts.LON2, e['t2'], consts.LAT3, consts.LON3, e['t3'])[1]

        (t12, t13) = delay_by_crosscorrelation(e)
        e['azimuth2'] = angles_calc(consts.LAT1, consts.LON1, e['t1'],
                                    consts.LAT2, consts.LON2, e['t1'] - t12,
                                    consts.LAT3, consts.LON3, e['t1'] - t13)[1]

    return events