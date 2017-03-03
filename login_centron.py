# -*- coding: utf-8 -*-


import requests
import re

MYTIMEOUT = 3


def test_centron(url, username, password):
    try:
        s = requests.session()
        myheader = {
            'Accept': 'text/html,application/xhtml+xml, application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/36.0.1979.0 Safari/537.36',
        }

        s.get(url, headers=myheader, timeout=MYTIMEOUT)

        params = {
            'useralias': username,
            'password': password,
            'submit': 'Connect >>'
        }

        r = s.post(url + '/index.php', headers=myheader, data=params, timeout=MYTIMEOUT)
        if r.status_code != 200:
            # print r.status_code
            return False
        else:
            results = re.findall('"(AjaxBankBasic)"', r.text.replace('\n', ''))
            # print results
            if len(results) > 0:
                return True
            return False
    except:
        return False


def login_centron(url, username, password):
    s = requests.session()
    myheader = {
        'Accept': 'text/html,application/xhtml+xml, application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/36.0.1979.0 Safari/537.36',
    }

    r = s.get(url, headers=myheader, timeout=MYTIMEOUT)
    sid = r.cookies['PHPSESSID']

    params = {
        'useralias': username,
        'password': password,
        'submit': 'Connect >>'
    }

    r = s.post(url + '/index.php', headers=myheader, data=params, timeout=MYTIMEOUT)

    # service
    critical_url = url + '/include/monitoring/status/Services/xml/ndo/serviceXML.php?&sid=' + sid \
                   + '&search=&search_host=&search_output=&num=0&limit=30&sort_type=last_state_change&order=ASC' \
                     '&date_time_format_status=d/m/Y%20H:i:s&o=svc_unhandled&p=20215&host_name=&nc=0&criticality=0'
    criticle_xml = s.get(critical_url, headers=myheader, timeout=MYTIMEOUT).text
    re_num_rows = re.findall('<numrows><!\[CDATA\[(.*?)\]\]></numrows>', criticle_xml)
    re_host = re.findall('<hnl><!\[CDATA\[(.*?)\]\]></hnl>', criticle_xml)
    re_service = re.findall('<sd><!\[CDATA\[(.*?)\]\]></sd>', criticle_xml)
    re_status = re.findall('<cs><!\[CDATA\[(.*?)\]\]></cs>', criticle_xml)
    re_duration = re.findall('<d><!\[CDATA\[(.*?)\]\]></d>', criticle_xml)
    re_lastcheck = re.findall('<lc><!\[CDATA\[(.*?)\]\]></lc>', criticle_xml)
    re_info = re.findall('<po><!\[CDATA\[(.*?)\]\]></po>', criticle_xml)
    num_rows = int(re_num_rows[0][0])

    centron_service = []  # [(host, service, status, duration, lastcheck, info)] status=CRITICAL/WARNING
    for i in range(0, num_rows):
        centron_service.append((re_host[i], re_service[i], re_status[i],
                                    re_duration[i], re_lastcheck[i], re_info[i]))

    # host
    critical_url = url + '/include/monitoring/status/Hosts/xml/ndo/hostXML.php?sid=' + sid \
                   + '&search=&num=0&limit=30&sort_type=last_state_change&order=ASC' \
                     '&date_time_format_status=d/m/Y%20H:i:s&o=h_unhandled&p=20105&time=1479795993&criticality=0'
    criticle_xml = s.get(critical_url, headers=myheader, timeout=MYTIMEOUT).text
    re_num_rows = re.findall('<numrows><!\[CDATA\[(.*?)\]\]></numrows>', criticle_xml)
    re_host = re.findall('<hnl><!\[CDATA\[(.*?)\]\]></hnl>', criticle_xml)
    re_status = re.findall('<cs><!\[CDATA\[(.*?)\]\]></cs>', criticle_xml)
    re_duration = re.findall('<lsc><!\[CDATA\[(.*?)\]\]></lsc>', criticle_xml)
    re_lastcheck = re.findall('<lc><!\[CDATA\[(.*?)\]\]></lc>', criticle_xml)
    re_info = re.findall('<ou><!\[CDATA\[(.*?)\]\]></ou>', criticle_xml)
    num_rows = int(re_num_rows[0][0])

    centron_host = []  # [(host, status, duration, lastcheck, info)] status=CRITICAL/WARNING
    for i in range(0, num_rows):
        centron_host.append((re_host[i], re_status[i], re_duration[i], re_lastcheck[i], re_info[i]))

    centron_results = {
        'service': centron_service,  # [(host, service, status, duration, last_check, info)]
        'host': centron_host  # [(host, status, duration, last_check, info)]
    }

    return centron_results


if __name__ == '__main__':
    url = 'http://*.*.*.*/centreon'
    username = 'admin'
    password = '*****'
    print login_centron(url, username, password)
