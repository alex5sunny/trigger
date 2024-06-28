from matplotlib import pyplot
import obspy
import numpy as np

pyplot.ion()
figure = pyplot.figure()

st = obspy.read()
while True:
    for i in range(len(st)):
        st[i].data = np.append(st[i].data[10:], st[i].data[:10])
    pyplot.clf()
    st.plot(fig=figure)
    pyplot.show()
    pyplot.pause(.01)
