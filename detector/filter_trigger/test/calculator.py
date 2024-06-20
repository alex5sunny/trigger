import math

llat_1 = 56.17258888
llong_1 = 37.1101722
t_1 = float(input('t1= (0.5)') or .5)

llat_2 = 56.1722611
llong_2 = 37.10723889
t_2 = float(input('t2= (1.0)') or 1.0)

llat_3 = 56.1729833
llong_3 = 37.10795278
t_3 = float(input('t3= (1.5)') or 1.5)

rad = 6363418

if t_1 > t_2 and t_2 > t_3:
    t2 = t_1
    llat2 = llat_1
    llong2 = llong_1
    t3 = t_2
    llat3 = llat_2
    llong3 = llong_2
    t1 = t_3
    llat1 = llat_3
    llong1 = llong_3

if t_1 > t_3 and t_3 > t_2:
    t2 = t_1
    llat2 = llat_1
    llong2 = llong_1
    t3 = t_3
    llat3 = llat_3
    llong3 = llong_3
    t1 = t_2
    llat1 = llat_2
    llong1 = llong_2

if t_2 > t_1 and t_1 > t_3:
    t2 = t_2
    llat2 = llat_2
    llong2 = llong_2
    t3 = t_1
    llat3 = llat_1
    llong3 = llong_1
    t1 = t_3
    llat1 = llat_3
    llong1 = llong_3

if t_2 > t_3 and t_3 > t_1:
    t2 = t_2
    llat2 = llat_2
    llong2 = llong_2
    t3 = t_3
    llat3 = llat_3
    llong3 = llong_3
    t1 = t_1
    llat1 = llat_1
    llong1 = llong_1

if t_3 > t_2 and t_2 > t_1:
    t2 = t_3
    llat2 = llat_3
    llong2 = llong_3
    t3 = t_2
    llat3 = llat_2
    llong3 = llong_2
    t1 = t_1
    llat1 = llat_1
    llong1 = llong_1

if t_3 > t_1 and t_1 > t_2:
    t2 = t_3
    llat2 = llat_3
    llong2 = llong_3
    t3 = t_1
    llat3 = llat_1
    llong3 = llong_1
    t1 = t_2
    llat1 = llat_2
    llong1 = llong_2

lat1 = llat1 * math.pi / 180.
lat2 = llat2 * math.pi / 180.
lat3 = llat3 * math.pi / 180.
long1 = llong1 * math.pi / 180.
long2 = llong2 * math.pi / 180.
long3 = llong3 * math.pi / 180.

cl1 = math.cos(lat1)
cl2 = math.cos(lat2)
cl3 = math.cos(lat3)
sl1 = math.sin(lat1)
sl2 = math.sin(lat2)
sl3 = math.sin(lat3)

# вычисляем стороны первого треугольника
delta12 = long2 - long1
cdelta12 = math.cos(delta12)
sdelta12 = math.sin(delta12)

y12 = math.sqrt(math.pow(cl2 * sdelta12, 2) + math.pow(cl1 * sl2 - sl1 * cl2 * cdelta12, 2))
x12 = sl1 * sl2 + cl1 * cl2 * cdelta12
ad12 = math.atan2(y12, x12)
l_2 = ad12 * rad

delta13 = long3 - long1
cdelta13 = math.cos(delta13)
sdelta13 = math.sin(delta13)

y13 = math.sqrt(math.pow(cl3 * sdelta13, 2) + math.pow(cl1 * sl3 - sl1 * cl3 * cdelta13, 2))
x13 = sl1 * sl3 + cl1 * cl3 * cdelta13
ad13 = math.atan2(y13, x13)
l_3 = ad13 * rad

delta23 = long3 - long2
cdelta23 = math.cos(delta23)
sdelta23 = math.sin(delta23)

y23 = math.sqrt(math.pow(cl3 * sdelta23, 2) + math.pow(cl2 * sl3 - sl2 * cl3 * cdelta23, 2))
x23 = sl2 * sl3 + cl2 * cl3 * cdelta23
ad23 = math.atan2(y23, x23)
l_1 = ad23 * rad

# вычисляем альфа1
cos_omega = (l_3 ** 2 - l_2 ** 2 - l_1 ** 2) / (-2 * l_1 * l_2)
omega = math.acos(cos_omega)
tau_1 = t2 - t3
tau_2 = t2 - t1

tan_b1 = ((tau_2 * l_1) / (tau_1 * l_2 * math.sin(omega)) - (math.tan(omega)) ** (-1))
b1 = math.atan(tan_b1) * 180 / (math.pi)
# угол1 =  56.169145020750015
if b1 < 0:
    b1 = b1 + 180
    print('угол1 = ', b1)
else:
    print('угол1 = ', b1)

# азимут 2-3
x = (cl2 * sl3) - (sl2 * cl3 * cdelta23)
y = sdelta23 * cl3
z = math.degrees(math.atan(-y / x))

if (x < 0):
    z = z + 180.

z2 = (z + 180.) % 360. - 180.
z2 = - math.radians(z2)
angle23 = (z2 - ((2 * math.pi) * math.floor((z2 / (2 * math.pi)))))
azimut23 = (angle23 * 180) / math.pi

# азимут 2-1
delta21 = long1 - long2
cdelta21 = math.cos(delta21)
sdelta21 = math.sin(delta21)
x = (cl2 * sl1) - (sl2 * cl1 * cdelta21)
y = sdelta21 * cl1
z = math.degrees(math.atan(-y / x))

if (x < 0):
    z = z + 180.

z21 = (z + 180.) % 360. - 180.
z21 = - math.radians(z21)
angle21 = (z21 - ((2 * math.pi) * math.floor((z21 / (2 * math.pi)))))
azimut21 = (angle21 * 180) / math.pi

if (azimut23 - azimut21) > 0:
    if (azimut23 - azimut21) < 180:
        azimut2S = azimut23 - b1
    else:
        azimut2S = azimut23 + b1
else:
    if (azimut21 - azimut23) < 180:
        azimut2S = azimut23 + b1
    else:
        azimut2S = azimut23 - b1

if azimut2S > 360:
    azimut2S = azimut2S - 360
if azimut2S < 0:
    azimut2S = 360 + azimut2S

# АЗИМУТ1 =  152.6545701416132
print('АЗИМУТ1 = ', azimut2S)

