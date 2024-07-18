from detector.misc.calc_angles import angles_calc

lat1 = 56.17258888
long1 = 37.1101722
t1 = float(input('t1= (1)') or 4.113)

lat2 = 56.1722611
long2 = 37.10723889
t2 = float(input('t2= (2)') or 3.943)

lat3 = 56.1729833
long3 = 37.10795278
t3 = float(input('t3= (3)') or 3.833)

b, azimut = angles_calc(lat1, long1, t1, lat2, long2, t2, lat3, long3, t3)

# АЗИМУТ1 =  152.6545701416132
# assert (int(azimut) == 152)
print('АЗИМУТ1 = ', azimut)
# угол1 =  56.169145020750015
b = (b + 180) % 180
# assert (int(b) == 56)
print('угол1 = ', b)
