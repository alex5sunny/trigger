import json
import logging
import os
import sys
from collections import defaultdict
from copy import deepcopy
from queue import Queue, Empty
from time import sleep

import numpy as np
from com_main_module import COMMON_MAIN_MODULE_CLASS
from obspy import UTCDateTime

sys.path.append(os.path.dirname(__file__))

import detector.misc.globals as glob
from detector.misc.misc_util import get_station_for_stream, split_params, split_streams, check_break, get_endtime, \
    append_to_graph, log
from detector.action.action_pipe import execute_action
from detector.filter_trigger.construct_triggers import construct_triggers

from backend.trigger_html_util import getTriggerParams, \
    save_triggers, save_sources, save_rules, save_actions, \
    get_actions_settings, get_rules_settings, get_sources_settings, set_source_streams
from detector.misc.globals import action_names_dic0, ActionType, ConnState

from detector.action.action_process import exec_actions, post_actions
from detector.filter_trigger.rule import rule_picker
from detector.misc.misc_util import fill_out_triggerings, append_test_triggerings, \
    to_actions_triggerings, group_triggerings

from detector.custom_processing.custom_processing import create_context, process_custom_data, remove_dups


class MAIN_MODULE_CLASS(COMMON_MAIN_MODULE_CLASS):

    def __init__(self, njsp, trigger_fxn, standalone=False):

        logger_config = {
            'logger_name': 'trigger',
            'file_name': 'trigger',
            'files_dir': '/media/sdcard/logs',
            'file_level': logging.DEBUG,
            'console_level': logging.DEBUG,  # if standalone else logging.WARN,
            'console_name': None if standalone else 'TRIGGER_MODULE'
        }

        config_params = {
            'config_file_name': 'trigger_module_cfg.json',
            # 'default_config': {'trigger_dir': '/var/lib/cloud9/trigger'}
        }

        web_ui_dir = os.path.join(os.path.dirname(__file__), "backend")
        # self._print('Initializing trigger module...')
        super().__init__(standalone, config_params, njsp, logger_config, web_ui_dir=web_ui_dir)
        self.message = 'starting...'
        config = self.get_config()
        # self._print('config:\n' + str(config) + '\n')
        self.restarting = False
        self.njsp = njsp

    def custom_web_ui_request(self, in_data):
        logger = glob.logger
        path = in_data['path']  # .split('?')
        for ext in ['jpg', 'png', 'ico', 'gif']:
            if path.endswith('.' + ext):
                f = open(self.web_ui_dir + os.sep + path, 'rb')
                data = f.read()
                f.close()
                return {'binary_content': data, 'code': 200,
                        'c_type': 'image/' + ext}
        if in_data['type'] == 'post':
            content = in_data['binary_content']
            response_dic = {}
            if content and path not in ['saveSources', 'applyActions']:
                request_dic = json.loads(content.decode())

            if path == 'initTrigger':
                response_dic = get_sources_settings()
            if path == 'trigger':
                triggers = request_dic['triggers']
                triggers_ids = [int(sid) for sid in triggers]
                triggerings_out = fill_out_triggerings(triggers_ids, glob.USER_TRIGGERINGS,
                                                       glob.LAST_TRIGGERINGS)
                response_dic['triggers'] = triggerings_out
            if path == 'rule':
                logger = logging.getLogger('glob')
                triggers = request_dic['triggers']
                triggers_ids = [int(sid) for sid in triggers]
                triggerings_out = fill_out_triggerings(triggers_ids, glob.USER_TRIGGERINGS,
                                                       glob.LAST_TRIGGERINGS)
                response_dic['triggers'] = triggerings_out
                rules = request_dic['rules']
                rules_ids = [int(sid) for sid in rules]
                rules_out = fill_out_triggerings(rules_ids, glob.URULES_TRIGGERINGS,
                                                 glob.LAST_RTRIGGERINGS)
                response_dic['rules'] = rules_out
                if glob.LIST_LOG:
                    response_dic['events'] = json.dumps(glob.LIST_LOG)
                if len(glob.GRAPH_DATA['ch1']):
                    response_dic['endtime'] = glob.GRAPH_DATA['endtime']
                    [response_dic.update({f'ch{i}': glob.GRAPH_DATA[f'ch{i}'].tolist()}) for i in range(1, 4)]
                    glob.GRAPH_DATA.clear()
            if path == 'initRule':
                params_list = getTriggerParams()
                trigger_dic = {params['ind']: params['name'] for params in params_list}
                response_dic = {'triggers': trigger_dic,
                                'actions': deepcopy(action_names_dic0)}
                actions_dic = get_actions_settings()
                # logger.debug(f'actions_dic:{actions_dic}')
                sms_dic = {sms_id: actions_dic[sms_id]['name'] for sms_id in actions_dic
                           if sms_id > 3}
                # logger.debug(f'sms_dic:{sms_dic}')
                response_dic['actions'].update(sms_dic)
                # logger.debug(f'from response_dic:{response_dic["actions"]}')
            if path == 'apply':
                response_dic = {'apply': 1}
                glob.restart = True
            if path == 'applyRules':
                session_id = request_dic['sessionId']
                html = request_dic['html']
                save_rules(html)
                self.restarting = glob.restart = True
            if path == 'save':
                session_id = request_dic['sessionId']
                html = request_dic['html']
                save_triggers(html)
                self.restarting = glob.restart = True
            if path == 'saveSources':
                save_sources(content.decode())
                self.restarting = glob.restart = True
            if path == 'applyActions':
                save_actions(content.decode())
                self.restarting = glob.restart = True
            if path == 'testActions':
                test_triggerings = {int(aid): v for aid, v in request_dic.items()}
                glob.TEST_TRIGGERINGS.update(test_triggerings)

            if response_dic:
                content = json.dumps(response_dic).encode()
            else:
                content = b''
            return {'binary_content': content, 'code': 200,
                    'c_type': 'application/json'}

    def main(self):
        workdir = os.path.dirname(__file__)
        config = self.get_config()

        if self.config.error:
            self.config.set_config(config)
            self.config.error = None
        logger = self.logger
        self.message = 'Starting...'
        base_params = {
            'reconnect': True,
            'reconnect_period': 30,
            'bson': True,
            'handshake': {
                'subscriptions': ['status', 'log', 'streams', 'alarms'],
                'flush_buffer': False,
                'client_name': 'NOTSET'
            }
        }

        while not self.shutdown_event.is_set():
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
            rules_settings_dic = rules_settings['rules_dic']
            coords = rules_settings['coords']

            sources = get_sources_settings()
            visited = set()
            for station in sources:
                njsp_params = deepcopy(base_params)
                njsp_params['handshake']['client_name'] = station
                conn_data = sources[station]
                host = conn_data['host']
                port = int(conn_data['port'])
                if (host, port) not in visited:
                    readers[station] = self.njsp.add_reader(host, port, station, njsp_params, njsp_queue)
                visited.add((host, port))

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
            custom_context = create_context()
            while not glob.restart and not self.shutdown_event.is_set():
                if glob.CONN_STATE != ConnState.CONNECTED:
                    self.message = glob.CONN_STATE.name.lower()
                elif any(glob.LAST_RTRIGGERINGS.values()):
                    self.message = 'TRIGGERED'
                else:
                    self.message = 'running'
                cur_time = UTCDateTime()
                try:
                    packets_data = njsp_queue.get(timeout=1)
                    check_time = cur_time
                    glob.CONN_STATE = ConnState.CONNECTED
                    for conn_name, dev_packets in packets_data.items():
                        # station = conn_name.split(':')[1]
                        host, port = conn_name.split(':')[-2:]
                        if host == '127.0.0.1':
                            host = 'localhost'
                        port = int(port)
                        q_interm = []
                        for packet_type, content in dev_packets.items():
                            if 'parameters' == packet_type:
                                streams_dict = {stream: (list(stdata['channels'].keys()), 'V')
                                                for stream, stdata in content['streams'].items()}
                                prev_dict = {station_dic['stream']: (station, station_dic['out port'])
                                             for station, station_dic in sources.items()
                                             if host == station_dic['host'] and port == station_dic['port']}
                                set_source_streams(host, port, streams_dict, prev_dict)
                                sources = get_sources_settings()
                                station_for_stream = get_station_for_stream(host, port, sources)
                                q_interm.extend(split_params(content, station_for_stream))
                            if 'streams' == packet_type:
                                station_for_stream = get_station_for_stream(host, port, sources)
                                q_interm.extend(split_streams(content, station_for_stream))
                        for packet_type, content in q_interm:
                            if 'parameters' == packet_type:
                                station = next(iter(content['streams']))
                                streamer_params = {'init_packet': {'parameters': content.copy()},
                                                   'ringbuffer_size': 10}
                                if station not in streamers:
                                    streamers[station] = \
                                        self.njsp.add_streamer('', sources[station]['out port'], streamer_params)
                                station_data = content['streams'][station]
                                sample_rates[station] = station_data['sample_rate']
                                chans = list(station_data['channels'].keys())
                                for chan in chans:
                                    ks[station][chan] = \
                                        station_data['channels'][chan]['counts_in_volt']
                                for trigger_list in triggers[station].values():
                                    for trigger in trigger_list:
                                        trigger.set_sample_rate(sample_rates[station])
                            if 'streams' == packet_type:
                                station = next(iter(content))
                                delta = 1. / sample_rates[station]
                                check_break(content, packets_q, delta, station)
                                glob.GRAPH_DATA['endtime'] = get_endtime(content, delta, station)
                                packets_q.append({packet_type: content})
                                starttime = UTCDateTime(content[station]['timestamp'])
                                if not custom_context['starttime']:
                                    custom_context['starttime'] = starttime
                                channels_data = content[station]['samples']
                                # logger.debug(f'ks keys:{list(ks[station].keys())}')
                                for chan, bytez in channels_data.items():
                                    k = ks[station][chan]
                                    data = np.frombuffer(bytez, 'int').astype('float') / k
                                    custom_context[chan] = np.append(custom_context[chan], data)
                                    glob.GRAPH_DATA[chan] = append_to_graph(glob.GRAPH_DATA[chan], data)
                                    for trigger in triggers.get(station, {}).get(chan, []):
                                        triggerings.extend(trigger.pick(starttime, data))
                    triggerings.sort()
                    # process triggerings and clear after that
                    for rule_id, rule_settings in rules_settings_dic.items():
                        rules_triggerings.extend(rule_picker(rule_id, triggerings,
                                                             rule_settings['triggers_ids'],
                                                             rule_settings['formula']))
                    rules_triggerings.sort()
                    # custom_picker(triggerings, glob.POSITIVES_TIMES, glob.RULE_TIMES, coords)
                    list_log = process_custom_data(custom_context, glob.DATA_BUF_DURATION, glob.DATA_SHIFT)
                    if list_log:
                        glob.logger.debug('list log:' + str(list_log))
                        glob.LIST_LOG.extend(list_log)
                        glob.LIST_LOG = remove_dups(glob.LIST_LOG)
                        glob.LIST_LOG[:-10] = []
                    # logger.debug(f'rules_triggerings:{rules_triggerings}')
                    to_actions_triggerings(rules_triggerings, rules_settings_dic, actions_triggerings)
                    actions_triggerings.sort(key=lambda dtr: (dtr[0], -dtr[1], dtr[2]))
                    group_triggerings(triggerings, glob.USER_TRIGGERINGS, glob.LAST_TRIGGERINGS)
                    group_triggerings(rules_triggerings, glob.URULES_TRIGGERINGS, glob.LAST_RTRIGGERINGS)
                except Empty:
                    if cur_time > check_time + 10:
                        glob.CONN_STATE = ConnState.NO_CONNECTION
                packets_q[:-glob.PBUF_SIZE] = []
                if any(glob.TEST_TRIGGERINGS.values()):
                    logger.debug(f'test triggerings:{glob.TEST_TRIGGERINGS}')
                append_test_triggerings(actions_triggerings, glob.TEST_TRIGGERINGS)
                # logger.debug(f'actions triggerings:{actions_triggerings}')
                exec_actions(actions_triggerings, counters, pet_times, actions_settings)
                post_actions(packets_q, self.njsp, sample_rates, counters, pet_times, actions_settings, streamers)
                triggerings.clear()
                rules_triggerings.clear()
                actions_triggerings.clear()

            conns = list(streamers.values()) + list(readers.values())
            for conn in conns:
                print(f'remove conn:{conn}')
                self.njsp.remove(conn)
            while set(conns) & set(self.njsp.handles):
                sleep(.1)

        self.module_alive = False
        self.message = 'Stopped'
        # self._print('Main thread exited')
