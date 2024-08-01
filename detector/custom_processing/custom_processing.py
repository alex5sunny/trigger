import numpy as np
from typing import List

from detector.custom_processing.find_events import find_events


def create_context() -> dict:
    return {'starttime': None,
            'ch1': np.asarray([], dtype='float'),
            'ch2': np.asarray([], dtype='float'),
            'ch3': np.asarray([], dtype='float')}


def process_custom_data(context: dict, data_buf_duration: int, data_shift: int) -> List[str]:
    res: List[str] = []
    chans = 'ch1 ch2 ch3'.split()
    while len(context['ch1']) > data_buf_duration:
        events = find_events(
            {
                't0': context['starttime'].datetime,
                **{chan: context[chan][:data_buf_duration] for chan in chans}
             },
            data_buf_duration
        )
        res.extend([f'{k}: {v}' for event in events for k, v in event.items() if k != 'data'])
        for chan in chans:
            context[chan] = context[chan][data_shift:]
        context['starttime'] += data_shift / 1000
    return res


def dics_to_log(dics_log: List[dict]) -> str:
    res = ''
    for dic_log in dics_log:
        for ke, val in dic_log.items():
            res += f'{ke}: {val}\n'
        res += '\n'
    return res
