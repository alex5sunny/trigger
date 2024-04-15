from obspy import UTCDateTime
from detector.action.action_pipe import execute_action
from detector.misc.globals import ActionType, logger
import detector.misc.globals as glob
from detector.misc.misc_util import get_packet_for_log


def exec_actions(actions_triggerings, counters, pet_times, actions_settings):
    for date_time, triggering, action_id in actions_triggerings:
        # logger.debug(f'TEST_TRIGGERINGS:{glob.TEST_TRIGGERINGS}\n'
        #              f'action_id:{action_id} triggering:{triggering}')
        action_settings = actions_settings[action_id]
        main_action(action_id, triggering, date_time, pet_times, counters,
                    action_settings.get('pem', 0),
                    action_settings.get('pet', 0),
                    action_settings.get('inverse', False),
                    action_settings.get('message', None),
                    action_settings.get('address', None))


def get_timing(streams_packet, sample_rates):
    stream_name = list(streams_packet['streams'].keys())[0]
    starttime = streams_packet['streams'][stream_name]['timestamp']
    sample_rate = sample_rates[stream_name]
    n_samples = len(list(streams_packet['streams'][stream_name]['samples'].values())[0]) // 4
    endtime = starttime + n_samples / sample_rate
    return starttime, endtime


def main_action(action_id, triggering, ttime, pet_times, counters, pem, pet, inverse, action_message, action_address):
    counters[action_id] += triggering
    if counters[action_id] < 0:
        raise Exception('more detriggerings than triggerings')
    if triggering == counters[action_id] == 1 and not pet_times[action_id]:
        if action_id == ActionType.send_SIGNAL.value:
            glob.pem_time = ttime - pem
        else:
            execute_action(action_id, 1, inverse, action_message, action_address)
    pet_times[action_id] = ttime + pet  # обновляется при всех срабатываниях


def post_action(action_id: int, packets_q: list, pet_times: dict, counters: dict,
                inverse, action_message, action_address, njsp, sample_rates, streamers):
    if action_id == ActionType.send_SIGNAL.value:
        endtime = get_timing(packets_q[0], sample_rates)[0] if packets_q else None
        while packets_q and endtime < pet_times[action_id]:
            streams_packet = packets_q.pop(0)
            starttime, endtime = get_timing(streams_packet, sample_rates)
            station, = streams_packet['streams'].keys()
            if endtime > glob.pem_time:
                njsp.broadcast_data(streamers[station], streams_packet)
        if pet_times[action_id] and endtime and endtime > pet_times[action_id]:
            pet_times[action_id] = 0
    elif not counters[action_id] and pet_times[action_id] and UTCDateTime() > pet_times[action_id]:
        execute_action(action_id, 0, inverse, action_message, action_address)
        pet_times[action_id] = 0


def post_actions(packets_q: list, njsp, sample_rates: dict, counters: dict, pet_times: dict,
                 actions_settings: dict, streamers: dict):
    for action_id, pet_time in pet_times.items():
        if not pet_time:
            continue    # turned off
        action_settings = actions_settings[action_id]
        post_action(action_id, packets_q, pet_times, counters,
                    action_settings.get('inverse', False),
                    action_settings.get('message', None),
                    action_settings.get('address', None), njsp, sample_rates, streamers)

