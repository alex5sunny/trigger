import logging

from copy import deepcopy
from datetime import datetime

import numpy as np
from obspy import UTCDateTime

logger = logging.getLogger('glob')


def get_expr(formula_list, triggers_dic):
    expr_list = []
    for i in range(len(formula_list)):
        expr_item = formula_list[i]
        if i % 2:
            expr_list.append(expr_item)
        else:
            val = triggers_dic[expr_item]
            expr_list.append(str(val))
    return ' '.join(expr_list)


def group_triggerings(triggerings, user_triggerings, last_triggerings={}):
    for date_time, triggering, trigger_id in triggerings:
        last_triggerings[trigger_id] = triggering
        user_triggerings[trigger_id].append(triggering)
        user_triggerings[trigger_id][:-10] = []


def fill_out_triggerings(triggers_ids, user_triggerings, last_triggerings):
    triggerings_out = {}
    for trigger_id in triggers_ids:
        if user_triggerings[trigger_id]:
            triggerings_out[trigger_id] = user_triggerings[trigger_id].pop(0)
        else:
            triggerings_out[trigger_id] = last_triggerings[trigger_id]
    return triggerings_out


def to_actions_triggerings(rules_triggerings, rules_settings, actions_triggerings):
    for date_time, triggering, rule_id in rules_triggerings:
        for action_id in rules_settings[rule_id]['actions']:
            actions_triggerings.append((date_time, 1 if triggering else -1, action_id))


def append_test_triggerings(actions_triggerings, test_triggerings):
    for action_id in test_triggerings:
        triggering = test_triggerings[action_id]
        actions_triggerings.append((float(UTCDateTime()), triggering, action_id))
        if triggering == 1:
            test_triggerings[action_id] = -1
        if triggering == -1:
            test_triggerings[action_id] = 0


def to_action_rules(rule_actions):
    action_rules = {}
    for rule, actions in rule_actions.items():
        for action in actions:
            if action not in action_rules:
                action_rules[action] = []
            action_rules[action].append(rule)
    return action_rules


def get_station_for_stream(host: str, port: int, sources: dict) -> dict:
    return {station_data['stream']: station for station, station_data in sources.items()
            if host == station_data['host'] and port == station_data['port']}


def split_params(content: dict, station_for_stream: dict) -> list:
    out = []
    for stream, stream_data in content['streams'].items():
        content_out = deepcopy(content)
        content_out['streams'] = {station_for_stream[stream]: stream_data}
        content_out['device_sn'] = station_for_stream[stream]
        out.append(('parameters', content_out))
    return out


def split_streams(content: dict, station_for_stream: dict) -> list:
    return [('streams', {station_for_stream[stream]: stream_data}) for stream, stream_data in content.items()]


def get_packet_for_log(content: dict) -> dict:
    content_log = deepcopy(content)
    for stream in content_log['streams']:
        for ch in content_log['streams'][stream]['samples']:
            content_log['streams'][stream]['samples'][ch] = len(content_log['streams'][stream]['samples'][ch])
    return content_log


def check_break(content: dict, packets_q: list, delta: float, station: str) -> [bool, str]:
    starttime = UTCDateTime(content[station]['timestamp'])
    for i in range(len(packets_q)):
        prev_content = packets_q[-1-i]['streams']
        prev_station = next(iter(prev_content))
        if station == prev_station:
            station_data = prev_content[station]
            prevtime = UTCDateTime(station_data['timestamp'])
            npts = len(next(iter(station_data['samples'].values()))) // 4
            prevtime += npts * delta
            if abs(prevtime - starttime) > delta:
                logger.warning(f'packets break, starttime:{starttime} prevtime:{prevtime} station:{station} '
                               f'npts:{npts}')
            else:
                pass
                # logger.debug(f'no break, starttime:{starttime} prevtime:{prevtime} station:{station}')
            return
    logger.debug(f'no prev packet, station:{station}')


def get_endtime(content: dict, delta: float, station: str) -> str:
    station_data = content[station]
    starttime = UTCDateTime(station_data['timestamp'])
    npts = len(next(iter(station_data['samples'].values()))) // 4
    return str((starttime + delta * (npts - 1)).datetime)


def append_to_graph(prev_data: np.ndarray, new_data: np.ndarray) -> np.ndarray:
    res = np.append(prev_data, new_data.astype('float32'))
    return res if len(res) <= 5000 else res[-1000:]


def get_logger() -> logging.Logger:
    return logger

