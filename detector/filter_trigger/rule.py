import detector.misc.globals as glob

from detector.misc.misc_util import get_expr


def rule_picker(rule_id, triggerings, triggers_ids, formula_list):
    rules_triggerings = []
    vals_dic = {trigger_id: glob.LAST_TRIGGERINGS[trigger_id] for trigger_id in triggers_ids}
    prev_val = glob.LAST_RTRIGGERINGS[rule_id]
    for date_time, triggering, trigger_id in triggerings:
        if trigger_id not in triggers_ids:
            continue
        vals_dic[trigger_id] = triggering
        rule_expr = get_expr(formula_list, vals_dic)
        rule_val = int(eval(rule_expr))
        # logger.debug(f'trigger_id:{trigger_id} triggering:{triggering} rule_id:{rule_id} '
        #              f'rule val:{rule_val} rule expr:{rule_expr}')
        if rule_val != prev_val:
            rules_triggerings.append((date_time, rule_val, rule_id))
            prev_val = rule_val
    return rules_triggerings


def custom_picker(triggerings: list[tuple], positives_times: dict, rule_times: dict):
    for date_time, triggering, trigger_id in triggerings:
        if not triggering:
            continue
        positives_times[trigger_id] = date_time
        if len(positives_times) >= 3 and \
                max(positives_times.values()) - min(positives_times.values()) <= 1 and \
                min(positives_times.values()) - max(rule_times.values()) > 1:
            rule_times.update(positives_times)
