import math


def l_calc(cl1, sl1, cl2, sl2, long1, long2):
    rad = 6363418
    delta12 = long2 - long1
    cdelta12 = math.cos(delta12)
    sdelta12 = math.sin(delta12)

    y12 = math.sqrt(math.pow(cl2 * sdelta12, 2) + math.pow(cl1 * sl2 - sl1 * cl2 * cdelta12, 2))
    x12 = sl1 * sl2 + cl1 * cl2 * cdelta12
    ad12 = math.atan2(y12, x12)
    l_2 = ad12 * rad
    return l_2, cdelta12, sdelta12


def angles_calc(lat1, long1, t1, lat2, long2, t2, lat3, long3, t3):
    (t1, lat1, long1), (t3, lat3, long3), (t2, lat2, long2) = \
        sorted(((t1, lat1, long1), (t2, lat2, long2), (t3, lat3, long3)))

    lat1, lat2, lat3, long1, long2, long3 = \
        [lat_lon * math.pi / 180. for lat_lon in (lat1, lat2, lat3, long1, long2, long3)]

    (cl1, sl1), (cl2, sl2), (cl3, sl3) = [(math.cos(lat), math.sin(lat)) for lat in (lat1, lat2, lat3)]

    l_2, _, _ = l_calc(cl1, sl1, cl2, sl2, long1, long2)
    l_3, _, _ = l_calc(cl1, sl1, cl3, sl3, long1, long3)
    l_1, cdelta23, sdelta23 = l_calc(cl2, sl2, cl3, sl3, long2, long3)

    # вычисляем альфа1
    cos_omega = (l_3 ** 2 - l_2 ** 2 - l_1 ** 2) / (-2 * l_1 * l_2)
    omega = math.acos(cos_omega)
    tau_1 = t2 - t3
    tau_2 = t2 - t1

    tan_b1 = ((tau_2 * l_1) / (tau_1 * l_2 * math.sin(omega)) - (math.tan(omega)) ** (-1))
    b1 = math.atan(tan_b1) * 180 / math.pi

    # азимут 2-3
    x = (cl2 * sl3) - (sl2 * cl3 * cdelta23)
    y = sdelta23 * cl3
    z = math.degrees(math.atan(-y / x))

    if x < 0:
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

    if x < 0:
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

    azimut2S = (azimut2S + 360) % 360
    return b1, azimut2S
