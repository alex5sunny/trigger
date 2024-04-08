from collections import defaultdict

import numpy as np
from obspy import UTCDateTime

import detector.misc.globals as glob
from detector.action.action_pipe import execute_action
from detector.filter_trigger.StaLtaTrigger import TriggerWrapper
from detector.filter_trigger.construct_triggers import construct_triggers
from detector.filter_trigger.rule import rule_picker
from detector.misc.globals import ActionType
from copy import deepcopy
from queue import Queue, Empty
from time import sleep

from backend.trigger_html_util import get_sources_settings, get_actions_settings, getTriggerParams, set_source_channels, get_rules_settings
from detector.action.action_process import exec_actions
from detector.misc.globals import logger, ConnState
from detector.misc.misc_util import group_triggerings, to_actions_triggerings, append_test_triggerings

base_params = {
    'reconnect': True,
    'reconnect_period': 10,
    'bson': True,
    'handshake': {
        'subscriptions': ['status', 'log', 'streams', 'alarms'],
        'flush_buffer': False,
        'client_name': 'NOTSET'
    }
}


def worker(njsp):

    while True:

        glob.restart = False
        njsp_queue = Queue(100)
        packets_q = []
        readers = {}
        streamers = {}
        sample_rates = {}

        counters = {}
        pet_times = {}
        ks = defaultdict(dict)

        triggerings = []
        rules_triggerings = []
        actions_triggerings = []

        rules_settings = get_rules_settings()

        sources = get_sources_settings()
        for station in sources:
            njsp_params = deepcopy(base_params)
            njsp_params['handshake']['client_name'] = station
            conn_data = sources[station]
            readers[station] = njsp.add_reader(conn_data['host'], int(conn_data['port']), station,
                                               njsp_params, njsp_queue)

        glob.TEST_TRIGGERINGS = {}
        actions_settings = get_actions_settings()
        for action_id in [ActionType.relay_A.value, ActionType.relay_B.value]:
            execute_action(action_id, 0, actions_settings[action_id].get('inverse', False))
        for action_id in actions_settings:
            counters[action_id] = pet_times[action_id] = 0
            glob.TEST_TRIGGERINGS[action_id] = 0
            # glob.TEST_TRIGGERINGS[action_id] = -1 if action_id in \
            #     [ActionType.relay_A.value, ActionType.relay_B.value] else 0

        triggers = construct_triggers(getTriggerParams())

        check_time = UTCDateTime()
        glob.CONN_STATE = ConnState.CONNECTING
        while not glob.restart:
            cur_time = UTCDateTime()
            try:
                packets_data = njsp_queue.get(timeout=1)
                check_time = cur_time
                glob.CONN_STATE = ConnState.CONNECTED
                for conn_name, dev_packets in packets_data.items():
                    station = conn_name.split(':')[1]
                    for packet_type, content in dev_packets.items():
                        packet_type, content = split_packet(packet_type, content, station)
                        if 'parameters' == packet_type and station not in streamers:
                            streamer_params = {'init_packet': {'parameters': content.copy()},
                                               'ringbuffer_size': 10}
                            streamers[station] = njsp.add_streamer('', sources[station]['out_port'],
                                                                   streamer_params)
                            station_data = content['streams'][station]
                            sample_rates[station] = station_data['sample_rate']
                            chans = list(station_data['channels'].keys())
                            set_source_channels(station, chans)
                            for chan in chans:
                                ks[station][chan] = \
                                    station_data['channels'][chan]['counts_in_volt']
                            for trigger_list in triggers[station].values():
                                for trigger in trigger_list:
                                    trigger.set_sample_rate(sample_rates[station])
                        if 'streams' == packet_type:
                            packets_q.append({packet_type: content})
                            starttime = UTCDateTime(content[station]['timestamp'])
                            channels_data = content[station]['samples']
                            # logger.debug(f'channels:{list(channels_data.keys())}')
                            for chan, bytez in channels_data.items():
                                k = ks[station][chan]
                                data = np.frombuffer(bytez, 'int').astype('float') / k
                                for trigger in triggers.get(station, {}).get(chan, []):
                                    triggerings.extend(trigger.pick(starttime, data))
                triggerings.sort()
                # process triggerings and clear after that
                for rule_id, rule_settings in rules_settings.items():
                    rules_triggerings.extend(rule_picker(rule_id, triggerings,
                                                         rule_settings['triggers_ids'],
                                                         rule_settings['formula']))
                rules_triggerings.sort()
                # logger.debug(f'rules_triggerings:{rules_triggerings}')
                to_actions_triggerings(rules_triggerings, rules_settings, actions_triggerings)
                actions_triggerings.sort()
                group_triggerings(triggerings, glob.USER_TRIGGERINGS, glob.LAST_TRIGGERINGS)
                group_triggerings(rules_triggerings, glob.URULES_TRIGGERINGS, glob.LAST_RTRIGGERINGS)
            except Empty:
                logger.warning('no data')
                if cur_time > check_time + 10:
                    glob.CONN_STATE = ConnState.NO_CONNECTION
            packets_q[:-glob.PBUF_SIZE] = []
            if any(glob.TEST_TRIGGERINGS.values()):
                logger.debug(f'test triggerings:{glob.TEST_TRIGGERINGS}')
            append_test_triggerings(actions_triggerings, glob.TEST_TRIGGERINGS)
            # logger.debug(f'actions triggerings:{actions_triggerings}')
            exec_actions(actions_triggerings, packets_q, njsp, sample_rates, counters,
                         pet_times, actions_settings, streamers)
            triggerings.clear()
            rules_triggerings.clear()
            actions_triggerings.clear()

        conns = list(streamers.values()) + list(readers.values())
        for conn in conns:
            njsp.remove(conn)
        while set(conns) & set(njsp.handles):
            sleep(.1)

