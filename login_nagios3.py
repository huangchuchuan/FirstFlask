# -*- coding: utf-8 -*-

import requests
import base64
from urlparse import *
import re

MYTIMEOUT = 3

def get_url_root(url):
    r = urlparse(url)

    if r.scheme:
        scheme = r.scheme
        root = r.netloc
        weburl = url
    else:
        scheme = 'http'
        root = r.path
        weburl = scheme + '://' + url
    return root, scheme, weburl


def test_nagios3(url, username, password):
    try:
        s = requests.session()
        auth = username + ':' + password
        auth = base64.b64encode(auth)

        myheader = {
            'Accept': 'text/html,application/xhtml+xml, application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/36.0.1979.0 Safari/537.36',
            'Authorization': 'Basic ' + auth
        }

        r = s.get(url, headers=myheader, timeout=MYTIMEOUT)
        if r.status_code != 200:
            return False
        else:
            results = re.findall('<title>(Nagios.*?)</title>', r.text.replace('\n', ''))
            if len(results) > 0:
                return True
            else:
                return False
    except:
        return False


def login_nagios3(url, username, password):
    s = requests.session()
    auth = username + ':' + password
    auth = base64.b64encode(auth)
    myheader = {
        'Accept': 'text/html,application/xhtml+xml, application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/36.0.1979.0 Safari/537.36',
        'Authorization': 'Basic '+auth
    }
    s.get(url, headers=myheader, timeout=MYTIMEOUT)
    root, scheme, weburl = get_url_root(url)
    # get services data
    service_url = scheme + '://' + root +'/nagios3/cgi-bin/status.cgi?host=all&servicestatustypes=28&limit=0'
    all_text = s.get(service_url, headers=myheader, timeout=MYTIMEOUT).text.replace('\n', '')
    all_text = all_text.replace('\n', '')
    # host_pattern = "<td align=left valign=center.*?><a .*?>(.*?)</a>"
    host_pattern = "<td align='left' valign=center.*?host=(.*?)&"
    service_pattern = "<td align='left' valign=center.*?><a .*?>(.*?)</a>"
    status_pattern = "<td class='status.*?'>([\w]+?)</td>"
    last_check_pattern = "<td class='status.*?' nowrap>([\d\s\-\:]+?)</td>"
    duration_pattern = "<td class='status.*?' nowrap>([\d\s\w]+?)</td>"
    info_pattern = "<td class='status.*?valign='center'>(.*?)</td>"
    host_results = re.findall(host_pattern, all_text)
    service_results = re.findall(service_pattern, all_text)
    status_results = re.findall(status_pattern, all_text)
    last_check_results = re.findall(last_check_pattern, all_text)
    duration_results = re.findall(duration_pattern, all_text)
    info_results = re.findall(info_pattern, all_text)
    nagios_service_results = []  # [(host,service,status,check_time,duration,info)] status=CRITICAL/WARNING/UNKNOWN
    length = len(host_results)
    for i in range(0, length):
        nagios_service_results.append((host_results[i], service_results[i], status_results[i],
                               last_check_results[i], duration_results[i], info_results[i]))
    # return True, nagios_service_results
    # get hosts data
    host_url = scheme + '://' + root + '/nagios3/cgi-bin/status.cgi?hostgroup=all&style=hostdetail&hoststatustypes=12&limit=0'

    all_text = s.get(host_url, headers=myheader, timeout=MYTIMEOUT).text.replace('\n', '')
    all_text = all_text.replace('\n', '')
    host_pattern = "<td align=left valign=center.*?><a .*?>(.*?)</a>"
    host_results = re.findall(host_pattern, all_text)
    status_results = re.findall(status_pattern, all_text)
    last_check_results = re.findall(last_check_pattern, all_text)
    duration_results = re.findall(duration_pattern, all_text)
    info_results = re.findall(info_pattern, all_text)
    nagios_host_results = []  # [(host,status,check_time,duration,info)]  status=UP/DOWN
    length = len(host_results)
    for i in range(0, length):
        nagios_host_results.append((host_results[i], status_results[i],
                               last_check_results[i], duration_results[i], info_results[i]))
    nagios_results = {
        'service': nagios_service_results,
        'host': nagios_host_results
    }
    return nagios_results


if __name__ == '__main__':
    url = 'http://*.*.*.*/nagios'
    # print get_url_root(url)
    username = 'admin'
    password = '*****'
    print login_nagios3(url=url, username=username, password=password)
    pass
