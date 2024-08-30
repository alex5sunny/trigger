import numpy as np
from typing import List

from detector.custom_processing.find_events import find_events
from detector.misc.misc_util import get_logger


def create_context() -> dict:
    return {'starttime': None,
            'ch1': np.asarray([], dtype='float'),
            'ch2': np.asarray([], dtype='float'),
            'ch3': np.asarray([], dtype='float')}


def process_custom_data(context: dict, data_buf_duration: int, data_shift: int) -> List[dict]:
    res: List[dict] = []
    chans = 'ch1 ch2 ch3'.split()
    while len(context['ch1']) > data_buf_duration:
        events = find_events(
            {
                't0': context['starttime'].datetime,
                **{chan: context[chan][:data_buf_duration] for chan in chans}
             },
            data_buf_duration
        )
        if events:
            get_logger().debug(f"t0:{context['starttime'].datetime} t1:{events[0]['t1']}")
        for event in events:
            event_dict = {}
            for k, v in event.items():
                if k != 'data':
                    event_dict[k] = str(v)[:-3] if k in 't1 t2 t3'.split() else f'{v:.2f}'
            res.append(event_dict)
        for chan in chans:
            context[chan] = context[chan][data_shift:]
        context['starttime'] += data_shift / 1000
    return res


def remove_dups(list_log: List[dict]) -> List[dict]:
    t_dict = {dic['t1']: tuple(dic.items()) for dic in list_log}
    return [dict(tup) for tup in sorted(t_dict.values())]
