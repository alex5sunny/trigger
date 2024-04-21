import inspect
import os
from collections import defaultdict
from copy import deepcopy

from lxml import etree

import backend
from detector.filter_trigger.trigger_types import TriggerType
from detector.misc.globals import ActionType, logger


def getHeaderDic(root):
    header_els = root.xpath('/html/body/table/tbody/tr/th')
    return {el.text: i for el, i in zip(header_els, range(100))}


def getTriggerParams():
    root = etree.parse(os.path.split(inspect.getfile(backend))[0] + '/triggers.html')
    header_inds = getHeaderDic(root)
    rows = root.xpath('/html/body/table/tbody/tr')[1:]
    params_list = []
    for row in rows:
        params_dic = {}
        for col in ['station', 'channel', 'trigger']:
            [params_dic[col]] = \
                [el.text for el in row[header_inds[col]].iter() if 'selected' in el.attrib]
        params_dic['trigger_type'] = TriggerType[params_dic.pop('trigger')]
        params_dic['use_filter'] = 'checked' in row[header_inds['filter']][0].attrib
        for cell_name in ['name', 'sta', 'lta', 'init_level', 'stop_level', 'freqmin', 'freqmax']:
            col_type = str if cell_name == 'name' else float if cell_name in ['stop_level', 'init_level'] \
                else int
            params_dic[cell_name] = col_type(row[header_inds[cell_name]][0].get('value'))
        params_dic['ind'] = int(row[header_inds['ind']].text.strip())
        params_list.append(params_dic)
    return params_list


def get_rules_settings():
    root = etree.parse(os.path.split(inspect.getfile(backend))[0] + '/rules.html')
    headers_dic = getHeaderDic(root)
    id_col = headers_dic['rule_id']
    formula_col = headers_dic['formula']
    actions_col = headers_dic['actions']
    rows = root.xpath('/html/body/table/tbody/tr')[1:]
    rule_dic = {}
    for row in rows:
        rule_id = int(row[id_col].text)
        rule_dic[rule_id] = {}
        formula_list = []
        for el in row[formula_col].iter():
            if 'selected' in el.attrib:
                if 'trigger_id' in el.attrib:
                    formula_list.append(int(el.attrib['trigger_id']))
                else:
                    formula_list.append(el.text)
        rule_dic[rule_id]['formula'] = formula_list
        rule_dic[rule_id]['triggers_ids'] = [formula_list[i]
                                             for i in range(0, len(formula_list), 2)]
        rule_dic[rule_id]['actions'] = [int(el.attrib['action_id'])
                                        for el in row[actions_col].iter()
                                        if 'selected' in el.attrib]
    return rule_dic


def get_sources_settings():
    root = etree.parse(os.path.split(inspect.getfile(backend))[0] + '/sources.html')
    headers_dic = getHeaderDic(root)
    station_col = headers_dic['station']
    host_col = headers_dic['host']
    port_col = headers_dic['port']
    stream_col = headers_dic['stream']
    outport_col = headers_dic['out port']
    channels_col = headers_dic['channels']
    units_col = headers_dic['units']
    rows = root.xpath('/html/body/table/tbody/tr')[1:]
    src_dic = {}
    for row in rows:
        # logger.debug('row:' + etree.tostring(row).decode())
        station = row[station_col][0].attrib['value'].strip()
        src_dic[station] = {}
        src_dic[station]['host'] = row[host_col][0].attrib['value'].strip()
        src_dic[station]['port'] = int(row[port_col][0].attrib['value'].strip())
        src_dic[station]['stream'] = row[stream_col].text.strip()
        src_dic[station]['out port'] = int(row[outport_col][0].attrib['value'].strip())
        src_dic[station]['channels'] = row[channels_col].text.split(' ')
        src_dic[station]['units'] = row[units_col].text.strip()
    return src_dic


def get_prev_dict(host: str, port: int) -> dict:
    src_dict = get_sources_settings()
    streams_dict = {}
    for station, station_dic in src_dict.items():
        stream = station_dic['stream']
        if host == station_dic['host'] and port == station_dic['port'] and stream not in streams_dict:
            streams_dict[stream] = (station, station_dic['out port'])
    return streams_dict


def get_station_name(port: int, stream: str, names: set) -> str:
    station0 = f'N{str(port)[-1]}{stream[:2].upper()}'
    if station0 not in names:
        return station0
    n = len(station0)
    for i in range(1, 100):
        istr = str(i)
        station = station0[:n - len(istr)] + istr
        if station not in names:
            return station
    raise Exception('cannot generate source name')


def set_source_streams(host: str, port: int, streams_dict: dict, prev_dict: dict):
    fpath = os.path.split(inspect.getfile(backend))[0] + '/sources.html'
    root = etree.parse(fpath)
    headers_dic = getHeaderDic(root)
    table = root.xpath('/html/body/table/tbody')[0]
    row = deepcopy(table[1])
    i = 1
    j = None
    while i < len(table):
        if host != table[i][headers_dic['host']][0].attrib['value'] or \
                port != int(table[i][headers_dic['port']][0].attrib['value']):
            i += 1
            continue
        if not j:
            j = i
        # print('table:\n', etree.tostring(table), '\nrow:\n', etree.tostring(table[i]))
        table.remove(table[i])
    for stream, (channels, units) in streams_dict.items():
        names = {row[headers_dic['station']][0].attrib['value'] for row in table[1:]}
        if stream in prev_dict:
            logger.debug(f'stream {stream} in prev_dict')
            station, outport = prev_dict[stream]
            if not station:
                station = get_station_name(port, stream, names)
        else:
            logger.debug(f'stream {stream} not in prev_dict')
            station = get_station_name(port, stream, names)
            if len(table) == 1:
                outport = 10011
            else:
                outport = 1 + max([int(row[headers_dic['out port']][0].attrib['value']) for row in table[1:]])
        logger.debug(f'set station {station}')
        row = deepcopy(row)
        row[headers_dic['station']][0].attrib['value'] = station
        row[headers_dic['host']][0].attrib['value'] = host
        row[headers_dic['port']][0].attrib['value'] = str(port)
        row[headers_dic['stream']].text = stream
        row[headers_dic['out port']][0].attrib['value'] = str(outport)
        row[headers_dic['channels']].text = ' '.join(channels)
        row[headers_dic['units']].text = units
        table.insert(j, row)
        j += 1
    root.write(fpath)


def get_action_data(action_type, root, id_col, address_col, message_col, name_col, additional_col):
    rows = root.xpath("//tr[./td/select/option[@selected]='" + action_type + "']")
    return {int(row[id_col].text): {'address': row[address_col][0].get('value'),
                                    'message': row[address_col][0].get('value'),
                                    'name': row[name_col][0].get('value'),
                                    'detrigger': 'checked' in row[additional_col][1].attrib}
            for row in rows}


def get_actions_settings():
    root = etree.parse(os.path.split(inspect.getfile(backend))[0] + '/actions.html')
    headers_dic = getHeaderDic(root)
    id_col = headers_dic['action_id']
    address_col = headers_dic['address']
    message_col = headers_dic['message']
    name_col = headers_dic['name']
    additional_col = headers_dic['additional']
    petA = int(root.xpath("//*[@id='petA']/@value")[0])
    petB = int(root.xpath("//*[@id='petB']/@value")[0])
    infiniteA = 'checked' in root.xpath("//*[@id='infiniteA']")[0].attrib
    infiniteB = 'checked' in root.xpath("//*[@id='infiniteB']")[0].attrib
    pet_inf = 60 * 60 * 24 * 365 * 10
    if infiniteA:
        petA = pet_inf
    if infiniteB:
        petB = pet_inf
    actions_dic = {ActionType.relay_A.value: {'name': 'relayA', 'pet': petA},
                   ActionType.relay_B.value: {'name': 'relayB', 'pet': petB}}
    pem = int(root.xpath("//input[@id='PEM']/@value")[0])
    pet = int(root.xpath("//input[@id='PET']/@value")[0])
    actions_dic[ActionType.send_SIGNAL.value] = {'name': 'seedlk', 'pem': pem, 'pet': pet}
    for row in root.xpath('/html/body/table/tbody/tr')[ActionType.send_SMS.value:]:
        sms_dic = {'name': row[name_col][0].get('value'),
                   'address': row[address_col][0].get('value'),
                   'message': row[message_col][0].get('value'),
                   'inverse': 'checked' in row[additional_col][1].attrib}
        actions_dic[int(row[id_col].text)] = sms_dic
    return actions_dic


def save_pprint_trig(xml, file):
    parser = etree.HTMLParser(remove_blank_text=True)
    tree = etree.fromstring(xml, parser).getroottree()
    header_inds = getHeaderDic(tree)
    rows = tree.xpath('/html/body/table/tbody/tr')[1:]
    # for row in rows:
    #     row[header_inds['val']].text = "<img src=\"img\\circle-gray.jpg\"/>"
    tree.write(file)


def save_pprint(xml, file):
    parser = etree.HTMLParser(remove_blank_text=True)
    tree = etree.fromstring(xml, parser).getroottree()
    tree.write(file)


def save_triggers(post_data_str):
    save_pprint_trig(post_data_str, os.path.split(inspect.getfile(backend))[0] + '/triggers.html')


def save_sources(post_data_str):
    save_pprint(post_data_str, os.path.split(inspect.getfile(backend))[0] + '/sources.html')


def save_rules(post_data_str):
    save_pprint(post_data_str, os.path.split(inspect.getfile(backend))[0] + '/rules.html')


def save_actions(post_data_str):
    save_pprint(post_data_str, os.path.split(inspect.getfile(backend))[0] + '/actions.html')


# def test_streams():
#     host = 'localhost'
#     port = 10000
#     prev_dict = get_prev_dict(host, port)
#     streams_dict = {'main': (list('123456'), 'V'), 'env': (list('123'), 'A')}
#     set_source_streams(host, port, streams_dict, prev_dict)
#
#
# test_streams()

# print(str(getTriggerParams()))

# print(getRuleFormulasDic())

# print(getChannels())
# save_pprint('<html><body>Hello<br/>World</body></html>', 'd:/temp/temp.xml')
# print(getTriggerParams())

# f = open('D:\\programming\\python\\Detector\\backend\\index.html', 'r')
# xml = f.read()
# f.close()
