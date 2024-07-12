from detector.misc.calc_angles import angles_calc

lat1 = 54
long1 = 36
t1 = float(input('t1= (0.5)') or .5)

lat2 = 52
long2 = 36
t2 = float(input('t2= (1.0)') or 1.0)

lat3 = 53
long3 = 35
t3 = float(input('t3= (1.5)') or 1.5)

b, azimut = angles_calc(lat1, long1, t1, lat2, long2, t2, lat3, long3, t3)

# АЗИМУТ1 =  152.6545701416132
# assert (int(azimut) == 152)
print('АЗИМУТ1 = ', azimut)
# угол1 =  56.169145020750015
b = (b + 180) % 180
# assert (int(b) == 56)
print('угол1 = ', b)
