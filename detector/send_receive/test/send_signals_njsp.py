import json
import logging
import time
from collections import OrderedDict

import numpy as np

from obspy import *
from matplotlib import pyplot

import sys

sys.path.append('/var/lib/cloud9/ndas_rt/sw_modules/trigger')

from detector.misc.header_util import chunk_stream, stream_to_dic
from detector.send_receive.njsp.njsp import NJSP
from detector.test.signal_generator import SignalGenerator
import os
import detector.misc as misc
import inspect


logpath = None
loglevel = logging.DEBUG

format = '%(levelname)s %(asctime)s %(funcName)s %(filename)s:%(lineno)d %(message)s'
logging.basicConfig(level=loglevel, filename=logpath, format=format)
logger = logging.getLogger('generator')

njsp = NJSP(logger=logger, log_level=logging.DEBUG)


def send_signal(st1, st2, port, units='V'):
    show_signal = False

    signal_generator1 = SignalGenerator(st1)
    signal_generator2 = SignalGenerator(st2)

    #context = zmq.Context()
    if show_signal:
        pyplot.ion()
        figure = pyplot.figure()
    st_vis = Stream()
    check_time = time.time()
    ch_dic  = {tr.stats.channel: {'ch_active': True, 'counts_in_volt': tr.stats.k} for tr in st1}
    ch_dic2 = {tr.stats.channel: {'ch_active': True, 'counts_in_volt': tr.stats.k} for tr in st2}
    parameters_dic = {
        'parameters': {
            'device_sn': 'NRAD',
            'device_model': 'NDAS-8426N v.1.20',
            'fw_version': '5.2 12.05.2024',
            'streams': {
                st1[0].stats.station: {
                    'sample_rate': int(st1[0].stats.sampling_rate),
                    'channels': ch_dic,
                    'data_format': 'bson'
                },
                st2[0].stats.station: {
                    'sample_rate': int(st2[0].stats.sampling_rate),
                    'channels': ch_dic2,
                    'data_format': 'bson'
                }
            }
        }
    }
    streamer_params = {'init_packet': parameters_dic, 'ringbuffer_size': 10}
    streamserver = njsp.add_streamer('', port, streamer_params)

    while True:
        st1 = signal_generator1.get_stream()
        st2 = signal_generator2.get_stream()
        st_add = st1.copy()
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
        for st12 in [st1, st2]:
            sts = chunk_stream(st12)
            bson_datas = [stream_to_dic(st, units) for st in sts]
            for bson_data in bson_datas:
                njsp.broadcast_data(streamserver, bson_data)
                # data_len = len(bson_data)
                # size_bytes = ('%08x' % data_len).encode()
                # sender.send(size_bytes + bson_data)
                time.sleep(.01)
        #print('broadcasted')
        time.sleep(.1)


base_path = os.path.split(inspect.getfile(misc))[0] + '/'
st = read(base_path + 'st1000.mseed')
for tr in st:
    tr.stats.k = 1000.0
st100 = read(base_path + 'st100.mseed')
for tr in st100:
    tr.stats.k = 10000
    tr.stats.network = 'RU'
    tr.stats.location = '00'
data = st[-1].data
st[-1].data = np.append(data[2000:], data[:2000])

print(st)
send_signal(st, st100, 10002)
