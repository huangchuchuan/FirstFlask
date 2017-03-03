# -*- coding: utf-8 -*-
from urlparse import *
import requests
import re
import shutil
import urllib
import hashlib
import os
# import ssl


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


def extra_url_ico(url, filepath):
    imgUrl = ''
    ispass = True

    myhead = {
        'User-Agent': 'Mozilla/5.0 (Windws NT 10.0;WOW64;rv:48.0) Gecko/20100101 Firefox/48.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip,deflate',
        'Upgrade-Insecure-Requests': '1',
    }

    r = urlparse(url)

    if r.scheme:
        scheme = r.scheme
        root = r.netloc
    else:
        scheme = 'http'
        root = r.path

    flag = False
    try:
        s = requests.session()
        r = s.get(url, headers=myhead, verify=False)
        rtext = r.text
        p = 'shortcut icon.*?href="(.*?)"'
        result = re.findall(p, rtext)
        if len(result) > 0:
            weburl = result[0]
        else:
            p = 'icon.*?href="(.*?)"'
            result = re.findall(p, rtext)
            weburl = result[0]

        # weburlfix = weburl[0:4]
        # # print weburlfix
        # if weburlfix == 'http':
        #     imgUrl = weburl
        #     # print imgUrl
        # else:
        #     imgUrl = scheme+"://"+root+weburl
            # print imgUrl
        if url[-1] != '/':
            if weburl[0] != '/':
                weburl = '/' + weburl
        imgUrl = url + weburl
        print imgUrl

        flag = True
    except Exception as e:
        print e
        ispass = False

    if not flag:
        try:
            imgUrl = scheme + '://' + root + '/favicon.ico'
            print imgUrl
            r = s.get(imgUrl, stream=True, headers=myhead, verify=False)
            if r.status_code == 200:
                flag = True
        except:
            ispass = False

        if not ispass:
            try:
                weburl = 'images/favicon.ico'
                if url[-1] != '/':
                    weburl = '/' + weburl
                imgUrl = url + weburl
                print imgUrl
                r = s.get(imgUrl, stream=True, headers=myhead, verify=False)
                if r.status_code == 200:
                    flag = True
                    ispass = True
            except:
                ispass = False
    if flag:
        try:
            # context = ssl._create_unverified_context()
            # urllib.urlretrieve(imgUrl, filepath+"/" + root + '.ico', context=context)
            r = s.get(imgUrl, stream=True, headers=myhead, verify=False)
            with open(filepath+"/" + root + '.ico', "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

        except Exception as e:
            flag = False
    if not flag:
        if ispass:
            shutil.copy(filepath+'/../pass.ico', filepath+"/" + root + '.ico')
        else:
            shutil.copy(filepath+'/../block.ico', filepath+"/" + root + '.ico')


def tranUnicode2Utf(data):
    if data[0] == 'u' and data[1] == '\'':
        data_decode = data[2:-1].decode('unicode-escape')
    else:
        data_decode = data
    return data_decode


def encrypt_password(password):
    encrypt = hashlib.md5()
    encrypt.update(password)
    return encrypt.hexdigest()


def create_user_dir(username, filepath):
    try:
        dirname = filepath + '/' + username.strip()
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        return True
    except Exception as e:
        print e
        return False


def delete_user_dir(username, filepath):
    try:
        dirname = filepath + '/' + username.strip()
        if os.path.isdir(dirname):
            shutil.rmtree(dirname)
        return True
    except Exception as e:
        print e
        return False


def update_user_dir(old_username, new_username, filepath):
    try:
        old_dirname = filepath + '/' + old_username.strip()
        new_dirname = filepath + '/' + new_username.strip()
        if os.path.isdir(old_dirname):
            os.rename(old_dirname, new_dirname)
        return True
    except Exception as e:
        print e
        return False


def get_nagios_tmplate():
    # [(host,service,status,check_time,duration,info)]
    nagios_service_table = '''
    <div class="table-responsive">
    <table class="table table-bordered" id="servicetable%s">
        <caption><a href="%s" target="_blank"><h4>%s - 服务状态</h4></a></caption>
        <thead>
            <tr>
                <th>主机</th>
                <th>服务</th>
                <th>状态</th>
                <th>上次检查</th>
                <th>持续时间</th>
                <th>信息</th>
            </tr>
        </thead>
        <tbody>%s</tbody>
    </table>
    </div>
    '''  # id,url,aliname,<tbody>

    nagios_service_tr_tp = '''
    <tr class="%s">
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
    </tr>
    '''  # active/success/warning/danger,host,service,status,lcheck,duration,info

    nagios_host_table = '''
    <div class="table-responsive">
    <table class="table table-bordered" id="hosttable%s">
        <caption><a href="%s" target="_blank"><h4>%s - 主机状态</h4></a></caption>
        <thead>
            <tr>
                <th>主机</th>
                <th>状态</th>
                <th>上次检查</th>
                <th>持续时间</th>
                <th>信息</th>
            </tr>
        </thead>
        <tbody>%s</tbody>
    </table>
    </div>
    '''  # id,url,aliname,<tbody>

    nagios_host_tr_tp = '''
    <tr class="%s">
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
    </tr>
    '''  # active/success/warning/danger,host,service,status,lcheck,duration,info

    return nagios_service_table, nagios_service_tr_tp, nagios_host_table, nagios_host_tr_tp


def get_cati_tmplate():
    # [(host, service, status, last_check, info)]
    cati_service_table = '''
    <div class="table-responsive">
    <table class="table table-bordered" id="servicetable%s">
        <caption><a href="%s" target="_blank"><h4>%s - 服务状态</h4></a></caption>
        <thead>
            <tr>
                <th>主机</th>
                <th>服务</th>
                <th>状态</th>
                <th>上次检查</th>
                <th>信息</th>
            </tr>
        </thead>
        <tbody>%s</tbody>
    </table>
    </div>
    '''  # id,url,aliname,<tbody>

    cati_service_tr_tp = '''
    <tr class="%s">
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
    </tr>
    '''  # active/success/warning/danger,host,service,status,lcheck,info

    cati_host_table = '''
    <div class="table-responsive">
    <table class="table table-bordered" id="hosttable%s">
        <caption><a href="%s" target="_blank"><h4>%s - 主机状态</h4></a></caption>
        <thead>
            <tr>
                <th>主机</th>
                <th>状态</th>
                <th>上次检查</th>
                <th>信息</th>
            </tr>
        </thead>
        <tbody>%s</tbody>
    </table>
    </div>
    '''  # id,url,aliname,<tbody>

    cati_host_tr_tp = '''
    <tr class="%s">
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
    </tr>
    '''  # active/success/warning/danger,host,status,lcheck,info

    return cati_service_table, cati_service_tr_tp, cati_host_table, cati_host_tr_tp


def get_collapse_tp():
    collapse_tp = '''
    <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-parent="#accordion"
          href="#collapse%s">
          %s <span class="badge">%s</span>
        </a>
      </h4>
    </div>
    <div id="collapse%s" class="panel-collapse collapse">
      <div class="panel-body">
        %s
      </div>
    </div>
    </div>
    '''  # id,aliname,num,id,<table>
    return collapse_tp


def judge_url_connect(url):
    try:
        requests.get(url, timeout=1)
        return True
    except:
        return False
