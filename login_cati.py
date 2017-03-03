# -*- coding: utf-8 -*-

import requests
import json
import re

MYTIMEOUT = 3

def test_cati(url, username, password):
    try:
        params = {
            'login_username': username,
            'login_password': password,
            'action': 'login'
        }

        s = requests.session()
        myheader = {
            'Accept': 'text/html,application/xhtml+xml, application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/36.0.1979.0 Safari/537.36',
        }
        s.get(url, headers=myheader, timeout=MYTIMEOUT)
        r = s.post(url, data=params, headers=myheader, timeout=MYTIMEOUT)

        if r.status_code != 200:
            return False
        else:
            results = re.findall('<title>(Console)</title>', r.text.replace('\n', ''))
            if len(results) > 0:
                return True
            return False
    except:
        return False


def login_cati(url, username, password):
    params = {
        'login_username': username,
        'login_password': password,
        'action': 'login'
    }

    s = requests.session()
    myheader = {
        'Accept': 'text/html,application/xhtml+xml, application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/36.0.1979.0 Safari/537.36',
    }
    s.get(url, headers=myheader, timeout=MYTIMEOUT)
    s.post(url, data=params, headers=myheader, timeout=MYTIMEOUT)

    # check hosts status
    cati_host_url = url + '/plugins/npc/npc.php?module=hosts&action=getHosts&p_state=not_ok'
    cati_host_response = s.post(cati_host_url, headers=myheader, timeout=MYTIMEOUT).text
    cati_host_json = json.loads(
        cati_host_response)  # {u'response': {u'value': {u'items': [], u'version': 1, u'total_count': 0}}}
    cati_host_items = cati_host_json['response']['value']['items']
    cati_host = []

    for cati_host_item in cati_host_items:
        host = cati_host_item['host_name']
        status = cati_host_item['state_type']
        last_check = cati_host_item['last_check']
        info = cati_host_item['output']
        cati_host.append((host, status, last_check, info))

    # check service status
    cati_service_url = url + '/plugins/npc/npc.php?module=services&action=getServices&p_state=not_ok'
    cati_service_response = s.post(cati_service_url, headers=myheader, timeout=MYTIMEOUT).text
    cati_service_json = json.loads(
        cati_service_response)  # {u'response': {u'value': {u'items': [], u'version': 1, u'total_count': 0}}}

    cati_service_items = cati_service_json['response']['value']['items']

    cati_service = []
    for cati_service_item in cati_service_items:
        host = cati_service_item['host_name']
        service = cati_service_item['service_description']
        status = cati_service_item['state_type']
        lastcheck = cati_service_item['last_check']
        info = cati_service_item['output']
        cati_service.append((host, service, status, lastcheck, info))

    cati_results = {
        'service': cati_service,  # [(host,service,status,last_check,info)]
        'host': cati_host  # [(host, status, last_check, info)]
    }
    return cati_results

if __name__ == '__main__':
    url = 'http://*.*.*.*/cacti'
    user = 'admin'
    password = '*****'
    print login_cati(url, user, password)
    pass
