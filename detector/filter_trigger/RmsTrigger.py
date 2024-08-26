import numpy as np

from detector.misc.globals import logger


class RmsTrigger:

    def __init__(self, n):
        self.n = n
        self.v = .0
        self.buf = np.require(np.zeros(n), dtype='float')

    def trigger(self, data):
        #logger.debug(f'max data:{max(abs(data))} min data:{min(abs(data))}')
        if data.size >= self.n:
            res1 = self.trigger(data[:self.n - 1])
            res2 = self.trigger(data[self.n - 1:])
            return np.append(res1, res2)
        if self.buf.size > self.n:
            decrement = self.buf[-self.n - 1]
        else:
            decrement = 0
        self.buf = self.buf[-self.n:]
        self.buf -= decrement
        cum_sum = np.cumsum(data**2)
        next_vals = self.v + (cum_sum - self.buf[-self.n:-self.n + data.size]) / self.n
        self.v = next_vals[-1]
        self.buf = np.append(self.buf, cum_sum+self.buf[-1])
        ret_val = np.sqrt(next_vals)
        #logger.debug('ret_val:' + str(max(ret_val)))
        return ret_val


class LevelTrigger:

    def __init__(self, npts: int, level: float):
        self.npts = npts
        self.level = level
        self.count = 0

    def trigger(self, data):
        if not self.npts:
            return data
        n = len(data)
        data_out = np.array([0.0] * n)
        i = 0
        while i < n:
            if self.count:
                if i + self.count >= n:
                    data_out[i:] = [self.level * 1.01] * (n - i)
                    self.count -= n - i
                else:
                    data_out[i:] = [self.level * 1.01] * self.count + [0] * (n - self.count - i)
                    self.count = 0
                break
            else:
                if data[i] >= self.level:
                    self.count = self.npts
                else:
                    offset = np.argmax(data[i:] >= self.level)
                    if offset:
                        data_out[i: i+offset] = [0.0] * offset
                        i += offset
                    else:
                        data_out[i:] = [0.0] * (n - i)
                        break
        return data_out


# class RmsTrigger:
#
#     def __init__(self, n):
#         self.triggerCore = RmsTriggerCore(n)
#         self.bufsize = 0
#
#     def trigger(self, data):
#         ret_val = self.triggerCore.trigger(data)
#         self.bufsize += data.size
#         tail = self.bufsize - self.triggerCore.nlta + 1
#         if 0 < tail < data.size:
#             ret_val = np.append(np.require(np.zeros(data.size - tail), dtype='float32'), ret_val[-tail:])
#         elif tail <= 0:
#             ret_val = np.require(np.zeros(data.size), dtype='float32')
#         return ret_val

# tr = read()[0]
# data = tr.data
# tr_trig = tr.copy()
# tr_trig.stats.station = 'trig'
# trigger_core = RmsTriggerCore(100)
# tr_trig.data = trigger_core.trigger(data)
# tr_tg02 = tr.copy()
# tr_tg02.stats.station = 'tg02'
# trigger_core = RmsTriggerCore(1000)
# tr_tg02.data = np.full(tr_tg02.stats.npts, 100., 'float32')
# tr_tg02.data = trigger_core.trigger(tr_tg02.data)
#
# (Stream() + tr_tg02 + tr_trig).plot()
# print(tr_tg02.data[:10])
# print(tr_tg02.data[10:20])
# print(tr_tg02.data[20:])
# print(tr_tg02.data[900:1000])
#
