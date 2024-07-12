import logging
import sys
import time
from pathlib import PurePath, Path

import numpy as np
from matplotlib import pyplot
from obspy import *

sys.path.append('/var/lib/cloud9/ndas_rt/sw_modules/trigger')

from detector.misc.header_util import chunk_stream, stream_to_dic
from detector.send_receive.njsp.njsp import NJSP
from detector.test.signal_generator import SignalGenerator
import os
import detector.misc as misc
import inspect

STATION = 'NRAD'

logpath = None
loglevel = logging.DEBUG

format = '%(levelname)s %(asctime)s %(funcName)s %(filename)s:%(lineno)d %(message)s'
logging.basicConfig(level=loglevel, filename=logpath, format=format)
logger = logging.getLogger('generator')

njsp = NJSP(logger=logger, log_level=logging.DEBUG)


def send_signal(st_cur, port, units='V'):
    show_signal = False

    signal_generator = SignalGenerator(st_cur)

    if show_signal:
        pyplot.ion()
        figure = pyplot.figure()
    st_vis = Stream()
    check_time = time.time()
    ch_dic = {tr.stats.channel:
                  {'ch_active': True, 'counts_in_volt': float(tr.stats.k)}
                  for tr in st_cur}

    parameters_dic = {
        'parameters': {
            'device_sn': STATION,
            'device_model': 'NDAS-8426N v.1.20',
            'fw_version': '5.2 12.05.2024',
            'streams': {
                st_cur[0].stats.station: {
                    'sample_rate': int(st_cur[0].stats.sampling_rate),
                    'channels': ch_dic,
                    'data_format': 'bson'
                }
            }
        }
    }
    streamer_params = {'init_packet': parameters_dic, 'ringbuffer_size': 10}
    streamserver = njsp.add_streamer('', port, streamer_params)

    while True:
        st_cur = signal_generator.get_stream()
        st_add = st_cur.copy()
        for tr_vis in st_add:
            tr_vis.data = np.require(tr_vis.data / tr_vis.stats.k, 'float32')
        st_vis += st_add
        cur_time = time.time()
        if cur_time > check_time + 1:
            check_time = cur_time
            st_vis.sort().merge()
            starttime = st_vis[0].stats.endtime - 5
            st_vis.trim(starttime=starttime)
            if show_signal:
                pyplot.clf()
                st_vis.plot(fig=figure)
                pyplot.show()
                pyplot.pause(.01)
            else:
                time.sleep(.1)  # delete this when return pyplot!
        sts = chunk_stream(st_cur)
        bson_datas = [stream_to_dic(st, units) for st in sts]
        for bson_data in bson_datas:
            njsp.broadcast_data(streamserver, bson_data)
            time.sleep(.01)
        time.sleep(.1)


def bin_to_stream(ch1_bin_path: PurePath, ch2_bin_path: PurePath, ch3_bin_path: PurePath) -> Stream:
    st = Stream()
    max_val = 0
    for i, bin_path in enumerate([ch1_bin_path, ch2_bin_path, ch3_bin_path]):
        tr = Trace(np.fromfile(bin_path, 'float32'))
        tr.stats.sampling_rate = 1000
        tr.stats.channel = f'ch{1 + i}'
        tr.stats.station = STATION
        max_val = max(max_val, max(abs(tr.data)))
        st += tr
    max_int = 2 ** 31
    k = max_int / max_val
    for tr in st:
        tr.data = (tr.data * k).astype('int32')
        tr.stats.k = k
    return st


base_path = 'e:/converter_data/Azimuth_from_saved_data/Record2_cut' #os.path.split(inspect.getfile(misc))[0] + '/'
st = bin_to_stream(base_path / Path('ch1.bin'), base_path / Path('ch2.bin'), base_path / Path('ch3.bin'))   # read(base_path + 'st1000.mseed')
# for tr in st:
#     tr.stats.k = 1000.0
# data = st[-1].data
# st[-1].data = np.append(data[2000:], data[:2000])

print(st)
send_signal(st, 10002)
