# -*- coding:utf-8 -*-

from flask import Flask
from flask_wtf.csrf import CsrfProtect
from flask import render_template
from flask import session, redirect, request, flash
from flask_wtf import Form
# import flask_whooshalchemy
from wtforms import StringField, PasswordField, SelectMultipleField, SelectField, validators
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from myutils import *
import login_cati, login_centron, login_nagios, login_nagios3
from flask import Markup
import sys, os
from flask import send_from_directory
from flask import abort
import json
import re


reload(sys)
sys.setdefaultencoding('utf8')

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/favicons')

app = Flask(__name__)
app.secret_key = '\x8d\xf9\x8d>\xf9\xd0S\xf2\x7f\xfflX\r\xaa\xd2\xa7\x8d\xcek\x04\x9e`\xfbmk\x88*\xb5\xfb\xf0\x06\xa5T\x87\xbc\xfd\x90\x96\xe5-\x07\x87Hh\xf5\x1f\xe1\xfe\xae\xf0\x19\xc4\xfa\x7f\xd5\xf9\xf53\x07e\xc0Z\x99_\xe7\xdf\x1d\x88\x16\xdb\x91\xcd+\xf5\x94\x91}\x16\xd4\xfb?Lp\xc5\x99YXUZ\x03o\xd5\xf5\xa8\x82\tPWGF\x86\x91\xcc\xeb\x97T\xfc\x90\xdf,:5n\xb7\x94\xa0$r\x82\x80\xa4\x17n7\xbd3\xc6 L]'
# csrf防护
csrf = CsrfProtect()
csrf.init_app(app)
# mysql数据库配置
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:ibcNqAsysu102@localhost:3306/sscc'
# app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:ibcNqAsysu102@10.12.0.5:3306/sscc'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']=True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app, use_native_unicode='utf-8') #实例化

# set the location for the whoosh index
app.config['WHOOSH_BASE'] = '/whoosh-base'


# link数据模型
class Link(db.Model):
    __tablename__ = 'link'

    urlid = db.Column(db.INT, primary_key=True, autoincrement=True)
    url = db.Column(db.String(255), nullable=False)
    descript = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False)


# User链接模型
class User(db.Model):
    __tablename__ = 'user'
    uid = db.Column(db.INT, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)


# Task事务模型
class Task(db.Model):
    __tablename__ = 'task'
    __searchable__ = ['title', 'type', 'begintime', 'endtime',
                      'phenomenon', 'status', 'author', 'customer', 'solution']
    tid = db.Column(db.INT, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    begintime = db.Column(db.TIMESTAMP, server_default=db.text('CURRENT_TIMESTAMP'))
    endtime = db.Column(db.TIMESTAMP, server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    phenomenon = db.Column(db.TEXT, nullable=True)
    status = db.Column(db.String(255), nullable=True)
    author = db.Column(db.String(255), nullable=True)
    customer = db.Column(db.String(255), nullable=False)
    solution = db.Column(db.String(255), nullable=True)


# Monitor数据模型
class Monitor(db.Model):
    __tablename__ = 'monitor'

    id = db.Column(db.INT, primary_key=True, autoincrement=True)
    url = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    aliname = db.Column(db.String(255), nullable=False)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


# 登录Form
class LoginForm(Form):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


# 新增链接的Form
class AddLinkForm(Form):
    weburl = StringField('weburl', validators=[DataRequired()])
    webdesc = StringField('webdesc', validators=[DataRequired()])


# 删除链接的Form
class DeleteLinkForm(Form):
    name_list = SelectMultipleField(u'网址', validators=[DataRequired()])


# 更新链接的Form
class UpdateLinkForm(Form):
    update_list = SelectField(u'网址', validators=[DataRequired()])
    update_url = StringField('updateurl')
    update_desc = StringField('updatedesc')


# 新增用户的Form
class AddUserForm(Form):
    username = StringField('username', validators=[DataRequired()])

    password1 = PasswordField('password1', [validators.DataRequired(), validators.EqualTo('password2', message=u'前后密码不一致')])
    password2 = PasswordField('password2', validators=[DataRequired()])


# 更新用户的Form
class UpdateUserForm(Form):
    user_list = SelectField('user_list', validators=[DataRequired()])
    username = StringField('username')
    password = PasswordField('password', validators=[DataRequired()])
    password1 = PasswordField('password1')
    password2 = PasswordField('password2')


# 删除用户的Form
class DeleteUserForm(Form):
    user_list = SelectField(u'用户名', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


# 增加事务的Form
class AddTaskForm(Form):
    title = StringField('title', validators=[DataRequired()])
    customer = StringField('customer', validators=[DataRequired()])
    task_type = SelectField('task_type', validators=[DataRequired()],
                            choices = [(u'故障', u'故障'), (u'变更', u'变更'), (u'需求', u'需求')], default=u'故障')
    phenomenon = StringField('phenomenon', validators=[DataRequired()])


# 删除事务的Form
class DelTaskForm(Form):
    tids = StringField('tids',  validators=[DataRequired()])


# 更新事务的Form
class UpdateTaskForm(Form):
    modifytid = StringField('modifytid', validators=[DataRequired()])
    modifyphenomenon = StringField('modifyphenomenon', validators=[DataRequired()])
    modifysolution = StringField('modifysolution', validators=[DataRequired()])
    modifystatus = SelectField('modifystatus', validators=[DataRequired()],
                             choices=[(u'处理中', u'处理中'), (u'已解决', u'已解决'), (u'将来解决', u'将来解决'), (u'无法解决', u'无法解决')])


# 新增监控的Form
class AddMonitorForm(Form):
    mon_url = StringField('monurl', validators=[DataRequired()])
    mon_username = StringField('mon_username', validators=[DataRequired()])
    mon_password = PasswordField('mon_password', validators=[DataRequired()])
    mon_type = SelectField('mon_type', validators=[DataRequired()],
                           choices=[('nagios', 'nagios'), ('nagios3', 'nagios3'),('centreon', 'centreon'), ('cacti', 'cacti')])
    mon_aliname = StringField('mon_aliname', validators=[DataRequired()])


# 删除监控的Form
class DeleteMonitorForm(Form):
    mon_list = SelectMultipleField(u'监控', validators=[DataRequired()])


# 更新监控的Form
class UpdateMonitorForm(Form):
    upmon_list = SelectField(u'监控', validators=[DataRequired()])
    upmon_url = StringField('mon_url')
    upmon_username = StringField('mon_username')
    upmon_password = PasswordField('mon_password')
    upmon_type = SelectField('mon_type', choices=[('nagios', 'nagios'), ('nagios3', 'nagios3'),('centreon', 'centreon'), ('cacti', 'cacti')], default='')
    upmon_aliname = StringField('mon_aliname')


# 认证跳转函数
def validate_user():
    if session.has_key('username'):
        if session['username'] is not '':
            return True
    return False


# 获得Task Model属性
def get_task_attr(attr_name):
    if attr_name == 'tid':
        return Task.tid
    if attr_name == 'title':
        return Task.title
    if attr_name == 'author':
        return Task.author
    if attr_name == 'phenomenon':
        return Task.phenomenon
    if attr_name == 'solution':
        return Task.solution
    if attr_name == 'type':
        return Task.type
    if attr_name == 'status':
        return Task.status
    if attr_name == 'begintime':
        return Task.begintime
    if attr_name == 'endtime':
        return Task.endtime
    if attr_name == 'customer':
        return Task.customer
    return None


# 读取link数据库到选择Form
def getWebUrls2SelectField(filter_username=None):
    obj_list = list()
    id_url_desc = list()
    i = 1
    default_id = None
    for obj in Link.query.order_by(Link.username):
        if filter_username == 'root':
            pass
        elif obj.username != filter_username:
            # print obj.username, filter_username
            continue
        if i == 1:
            default_id = obj.urlid
        obj_list.append((str(obj.urlid), str(i) + '. ' + obj.descript))
        id_url_desc.append((obj.url, obj.descript))
        i += 1
    return obj_list, default_id, id_url_desc


# 读取user数据库到选择Form
def getUsername2SelectForm(not_include_username=None):
    obj_list = list()
    i = 1
    default_id = None
    for obj in User.query:
        if obj.username == not_include_username:
            continue
        if i == 1:
            default_id = obj.uid
        obj_list.append((str(obj.uid), obj.username))
        i += 1
    return obj_list, default_id


# 读取monitor数据库到选择Form
def getMonitor2SelectField():
    obj_list = list()
    id_url_aliname = list()
    i = 1
    default_id = None
    for obj in Monitor.query.order_by(Monitor.aliname):
        if i == 1:
            default_id = obj.id
        obj_list.append((str(obj.id), str(i) + '. ' + obj.aliname))
        id_url_aliname.append((obj.url, obj.aliname))
        i += 1
    return obj_list, default_id, id_url_aliname


@csrf.error_handler
def csrf_error(reason):
    # 默认csrf错误页面
    if not validate_user(): return redirect('/login')
    return render_template('base.html', title=u'csrf错误页', username=session['username'], page_header='csrf错误页', page_body=reason), 403


@app.errorhandler(404)
def page_not_found(error):
    if not validate_user(): return redirect('/login')
    return render_template('base.html', title=u'404错误页', username=session['username'], page_header='404错误页', page_body=error), 404


@app.errorhandler(500)
def page_internal_error(error):
    if not validate_user(): return redirect('/login')
    return render_template('base.html', title=u'500错误页', username=session['username'], page_header='500错误页', page_body=error), 500


# 首页控制器
@app.route('/')
def index():
    if not validate_user(): return redirect('/login')
    return render_template('base.html', title=u'首页', username=session['username'], page_header='Welcome', page_body=u'欢迎使用'), 200


# 登录控制器
@app.route('/login', methods=['GET', 'POST'])
def login():
    session['alarm'] = 1
    form = LoginForm()
    if request.method == 'GET':
        if validate_user():
            return render_template('base.html', title=u'首页', username=session['username'], page_header='Welcome', page_body=u'欢迎使用'), 200
    else:
        if form.validate_on_submit():
            encrypt = hashlib.md5()
            encrypt.update(form.password.data)
            username = form.username.data
            password = encrypt.hexdigest()
            user_record = User.query.filter_by(username=username, password=password).first()
            if user_record:
                session['username'] = form.username.data
                return render_template('base.html', title=u'首页', username=session['username'], page_header='Welcome', page_body=u'欢迎使用'), 200
            else:
                form.errors['username'] = [u'账号或密码错误']

    return render_template('login.html', form=form), 200


# 登出控制器
@app.route('/logout', methods=['GET'])
def logout():
    if validate_user():
        session['username'] = ''
    return redirect('/login')


# 网址显示控制器
@app.route('/webs')
def webs():
    if not validate_user(): return redirect('/login')
    tmplate = '''
    <div class="col-sm-4 col-md-2" style="margin-bottom: 15px;">
        <div class="img-rounded text-center">
            <a href="%s" target="_blank">
                <img class="url-icon" alt="%s" src="static/favicons/%s">
                <div class="caption">%s</div>
            </a>
        </div>
    </div>

    '''

    weblinks = ''
    if session['username']=='root':
        links = Link.query.order_by(Link.username).all()
    else:
        links = Link.query.filter_by(username=(session['username']))
    i = 1
    usergroup = []
    for link in links:
        if link.username not in usergroup:
            usergroup.append(link.username)
            weblinks += '''
            <div class="col-lg-12">
                <h3 class="page-header">%s</h1>
            </div>

            '''% link.username
        root, scheme, weburl = get_url_root(link.url)
        if link.descript[0] == 'u' and link.descript[1] == '\'':
            link_desc = link.descript[2:-1].decode('unicode-escape')
        else:
            link_desc = link.descript
        weblinks += (tmplate % (weburl, link_desc, link.username.strip()+'/'+root+'.ico', str(i)+ '. ' + link_desc))
        i += 1
    if i>1:
        tmplate = '''

        <!-- delete image -->
        <div class="col-sm-4 col-md-2">
            <div class="img-rounded text-center">
                <a href="#" data-toggle="modal" data-target="#deleteModal">
                    <img class="url-icon" alt="Delete a link" src="static/favicons/delete.ico">
                    <div class="caption">点击删除链接</div>
                </a>
            </div>
        </div>
        <!-- /.delete image -->
        <!-- update image -->
        <div class="col-sm-4 col-md-2">
            <div class="img-rounded text-center">
                <a href="#" data-toggle="modal" data-target="#updateModal">
                    <img class="url-icon" alt="Update a link" src="static/favicons/update.ico">
                    <div class="caption">点击更新链接</div>
                </a>
            </div>
        </div>
        <!-- /.update image -->
        '''
        weblinks = tmplate+weblinks
    urls = Markup(weblinks)
    form = AddLinkForm()
    select_form = DeleteLinkForm()
    data_list, default_id, id_url_desc = getWebUrls2SelectField(session['username'])
    select_form.name_list.choices = data_list
    select_form.name_list.default = default_id
    update_form =  UpdateLinkForm()
    update_form.update_list.choices = data_list
    update_form.update_list.default = default_id
    # update_form.update_url.data = id_url_desc[0][0]
    # update_form.update_desc.data = tranUnicode2Utf(id_url_desc[0][1])
    return render_template('webs.html', title=u'网址', username=session['username'], page_header=u'网址',
                           urls=urls, form=form, select_form=select_form, update_form=update_form), 200


# 事务显示控制器
@app.route('/tasklist', methods=['GET', 'POST'])
def tasklist():
    if not validate_user(): return redirect('/login')
    if request.method=='GET':
        form = AddTaskForm()
        deltaskform = DelTaskForm()
        return render_template('showtasklist.html', title=u'事务', username=session['username'], page_header=u'事务',
                           form=form, deltaskform=deltaskform), 200
    else:

        limit = request.form.get('limit', None)
        offset = request.form.get('offset', None)
        if limit is None or offset is None:
            return 'wrong data'
        if limit == '' or offset == '':
            return 'wrong data'

        filter_data = request.form.get('filter', None)
        adv_sort = False

        # 获得排序参数
        sort_flag = request.form.get('sort', None)
        if sort_flag is None or sort_flag == '':
            # 高级排序
            adv_sort = True
            multisort_dict = {}
            p_sort = '(multiSort\[[0-9]+\])\[(sort.*)\]'

            for key in request.form:
                value = request.form[key]
                re_result = re.findall(p_sort, key)

                if len(re_result)>0:
                    if re_result[0][0] in multisort_dict:
                        multisort_dict[re_result[0][0]][re_result[0][1]] = value
                    else:
                        multisort_dict[re_result[0][0]] = {}
                        multisort_dict[re_result[0][0]][re_result[0][1]] = value
            # //print multisort_dict # {'multiSort[0]': {'sortOrder': u'desc', 'sortName': u'tid'}, 'multiSort[1]': {'sortOrder': u'asc', 'sortName': u'title'}}
        else:
            # 普通排序
            sort_name = sort_flag
            order = request.form.get('order', None)
            # print sort_name, order
        # 形成排序规则
        if not adv_sort:
            if order == 'asc':
                sort_order = get_task_attr(sort_name).asc()
            else:
                sort_order = get_task_attr(sort_name).desc()
        else:
            sort_order = None
            for level in multisort_dict:
                sortOrder = multisort_dict[level]['sortOrder']
                sortName = multisort_dict[level]['sortName']
                if sort_order is None:
                    sort_order = [get_task_attr(sortName).asc() if sortOrder == 'asc' else get_task_attr(sortName).desc()]
                else:
                    sort_order = sort_order.append(get_task_attr(sortName).asc() if sortOrder == 'asc' else get_task_attr(sortName).desc())
        # 形成搜索条件并进行数据库查询
        if filter_data is None or filter_data == '':
            # 普通搜索
            search = request.form.get('search', None)
            if search is not None and search:
                if len(re.findall('^[0-9:\-\s]+$', search)) > 0:
                    search_like='%'+search+'%'
                    all_tasks = Task.query.filter(Task.title.like(search_like) | Task.solution.like(search_like) |
                                              Task.type.like(search_like) | Task.status.like(search_like) |
                                              Task.author.like(search_like) | Task.customer.like(search_like) |
                                              Task.phenomenon.like(search_like) | Task.tid.like(search_like) |
                                              Task.begintime.like(search_like) | Task.endtime.like(search_like)).all()
                    tasks = Task.query.filter(Task.title.like(search_like) | Task.solution.like(search_like) |
                                              Task.type.like(search_like) | Task.status.like(search_like) |
                                              Task.author.like(search_like) | Task.customer.like(search_like) |
                                              Task.phenomenon.like(search_like) | Task.tid.like(search_like) |
                                              Task.begintime.like(search_like) | Task.endtime.like(search_like)
                                              ).order_by(sort_order).limit(limit).offset(offset).all()
                else:
                    search_like = '%' + search + '%'
                    all_tasks = Task.query.filter(Task.title.like(search_like) | Task.solution.like(search_like) |
                                              Task.type.like(search_like) | Task.status.like(search_like) |
                                              Task.author.like(search_like) | Task.customer.like(search_like) |
                                              Task.phenomenon.like(search_like) | Task.tid.like(search_like)
                                              ).all()
                    tasks = Task.query.filter(Task.title.like(search_like) | Task.solution.like(search_like) |
                                              Task.type.like(search_like) | Task.status.like(search_like) |
                                              Task.author.like(search_like) | Task.customer.like(search_like) |
                                              Task.phenomenon.like(search_like) | Task.tid.like(search_like)
                                              ).order_by(sort_order).limit(limit).offset(offset).all()
            else:
                all_tasks = Task.query.all()
                tasks = Task.query.order_by(sort_order).limit(limit).offset(offset).all()
        else:
            filter_data = json.loads(filter_data)
            search_like = None
            for f in filter_data:
                if f == 'begintime' or f == 'endtime':
                    if not len(re.findall('^[0-9:\-\s]+$', filter_data[f])) > 0:
                        continue
                elif f == 'tid':
                    if not len(re.findall('^[0-9]+$', filter_data[f])) > 0:
                        continue

                if search_like is None:
                    search_like = get_task_attr(f).like('%'+filter_data[f]+'%')
                else:
                    search_like = search_like & get_task_attr(f).like('%'+filter_data[f]+'%')
            all_tasks = Task.query.filter(search_like).all()
            tasks = Task.query.filter(search_like).order_by(sort_order).limit(limit).offset(offset).all()

        tasks_dict = {}
        tasks_dict['total'] = len(all_tasks)
        tasks_list = []
        for task in tasks:
            tasks_row_dict = {}
            tasks_row_dict["tid"] = task.tid
            tasks_row_dict["title"] = task.title
            tasks_row_dict["type"] = task.type
            tasks_row_dict["begintime"] = task.begintime.strftime('%Y-%m-%d %H:%M')
            endtime = task.endtime
            if endtime:
                tasks_row_dict["endtime"] = task.endtime.strftime('%Y-%m-%d %H:%M')
            else:
                tasks_row_dict["endtime"] = '0000-00-00 00:00:00'
            tasks_row_dict["phenomenon"] = task.phenomenon
            tasks_row_dict["status"] = task.status
            tasks_row_dict["author"] = task.author
            tasks_row_dict["customer"] = task.customer
            tasks_row_dict["solution"] = task.solution if task.solution else 'None'
            tasks_list.append(tasks_row_dict)
        tasks_dict['rows'] = tasks_list
        return json.dumps(tasks_dict)


# 增加事务控制器
@app.route('/addtask', methods=['POST'])
def addtask():
    if not validate_user(): return redirect('/login')
    form = AddTaskForm()
    if form.validate_on_submit():
        title = (request.form['title'])
        customer = (request.form['customer'])
        task_type = (request.form['task_type'])
        phenomenon = (request.form['phenomenon'])
        task = Task(title=title, customer=customer, type=task_type,
                    phenomenon=phenomenon, status=(u'处理中'), author=(session['username']))
        db.session.add(task)
        db.session.commit()
        flash(u'*成功增加记录')
    else:
        flash(u'各条目必须填写')
    return redirect('/tasklist')


# 删除事务控制器
@app.route('/deltask', methods=['POST'])
def deltask():
    if not validate_user(): return redirect('/login')
    form = DelTaskForm()
    if form.validate_on_submit():
        tids =  request.form['tids'].split(',')
        # //print tids
        for tid in tids:
            task = Task.query.filter_by(tid=tid).first()
            if task:
                if session['username'] != 'root':
                    if task.author != (session['username']):
                        flash(u'无权限删除用户 '+task.author+u' 的记录')
                    else:
                        db.session.delete(task)
                        flash(u'*成功删除记录 '+str(task.tid))
                else:
                    db.session.delete(task)
                    flash(u'*成功删除记录 '+str(task.tid))
                db.session.commit()
            else:
                flash(u'错误的输入')
    else:
        flash(u'错误的输入')
    return redirect('/tasklist')


# 更改事务控制器
@app.route('/updatetask', methods=['POST'])
def updatetask():
    if not validate_user(): return redirect('/login')
    # print request.data
    form = UpdateTaskForm()
    if form.validate_on_submit():
        tid = form.modifytid.data
        phenomenon = form.modifyphenomenon.data
        solution = form.modifysolution.data
        status = form.modifystatus.data
        task = Task.query.filter_by(tid=tid).first()
        if task:
            if session['username'] != 'root' and task.author != (session['username']):
                flash(u'无权限修改用户 '+task.author+u' 的记录')
            else:
                task.phenomenon = phenomenon
                task.solution = solution
                task.status = status
                flash(u'*成功修改记录 '+str(task.tid))
                db.session.commit()
        else:
            flash(u'错误的输入')
    else:
        flash(u'必须填写足够的参数')
    return redirect('/tasklist')


# 增加网址控制器
@app.route('/addlink', methods=['POST'])
def addlink():
    if not validate_user(): return redirect('/login')
    form = AddLinkForm()
    if form.validate_on_submit():
        weburl = request.form['weburl']
        webdesc = request.form['webdesc']
        extra_url_ico(weburl, UPLOAD_FOLDER+'/'+session['username'].strip())
        url = Link(url=weburl, descript=webdesc, username=session['username'])
        db.session.add(url)
        db.session.commit()
        flash(u'*成功增加链接 '+webdesc)
    else:
        flash(u'网址和名称必须填写')
    return redirect('/webs')


# 删除网址控制器
@app.route('/dellink', methods=['POST'])
def dellink():
    if not validate_user(): return redirect('/login')
    form = DeleteLinkForm()
    data_list, default_id, id_url_desc = getWebUrls2SelectField(session['username'])
    form.name_list.choices = data_list
    form.name_list.default = default_id
    if form.validate_on_submit():
        select_ids = form.name_list.data
        for select_id in select_ids:
            link = Link.query.filter_by(urlid=select_id).first()
            if link:
                if session['username'] == 'root':
                    db.session.delete(link)
                    flash(u'*成功删除 '+link.descript)
                elif session['username'] == link.username:
                    db.session.delete(link)
                    flash(u'*成功删除 ' + link.descript)
                else:
                    flash(u'无权限删除用户 '+link.username+u' 的链接')
        db.session.commit()
    else:
        flash(u'要删除的网址必须选择')
    return redirect('/webs')


# 更新网址控制器
@app.route('/updatelink', methods=['POST'])
def updatelink():
    if not validate_user(): return redirect('/login')
    update_form = UpdateLinkForm()
    data_list, default_id, id_url_desc = getWebUrls2SelectField(session['username'])
    update_form.update_list.choices = data_list
    update_form.update_list.default = default_id
    # update_form.update_url.data = id_url_desc[0][0]
    # update_form.update_desc.data = tranUnicode2Utf(id_url_desc[0][1])
    if update_form.validate_on_submit():
        update_id = update_form.update_list.data
        update_url = update_form.update_url.data
        update_desc = update_form.update_desc.data

        link = Link.query.filter_by(urlid=update_id).first()
        if link:
            if session['username'] != 'root' and session['username'] != link.username:
                # print session['username'], link.username
                flash(u'无权限修改用户 '+link.username+' 的链接')
            else:
                if update_url:
                    if update_url != link.url:
                        extra_url_ico(update_url, UPLOAD_FOLDER+'/'+session['username'].strip())
                    link.url = update_url
                if update_desc:
                    link.descript = update_desc
                db.session.commit()
                flash(u'*成功修改链接 '+link.descript)
        else:
            flash(u'错误输入')
    else:
        flash(u'内容不能为空')
    return redirect('/webs')


# 增加用户控制器
@app.route('/adduser', methods=['GET', 'POST'])
def adduser():
    if not validate_user(): return redirect('/login')
    if request.method == 'GET':
        form = AddUserForm()
        return render_template('adduser.html', title=u'增加用户', username=session['username'],
                               page_header=u'增加用户', form=form), 200
    elif request.method == 'POST':
        form = AddUserForm()
        if form.validate_on_submit():
            username = form.username.data.strip()
            password = request.form['password1']
            user = User.query.filter_by(username=username).first()
            if not user:
                create_flag = create_user_dir(username, UPLOAD_FOLDER)
                if create_flag:
                    user = User(username=username, password=encrypt_password(password))
                    db.session.add(user)
                    db.session.commit()
                    flash(u'*已成功增加用户 ' + username)
                else:
                    flash(u'增加用户 ' + username + u' 文件夹失败')
                form.username.data = ''
            else:
                flash(u'用户 '+username+' 已存在')
        else:
            flash(u'两次密码输入不一致')
        return render_template('adduser.html', title=u'增加用户', username=session['username'],
                               page_header=u'增加用户', form=form), 200
    else:
        abort(404)


# 更新用户控制器
@app.route('/updateuser', methods=['GET', 'POST'])
def updateuser():
    if not validate_user(): return redirect('/login')
    if request.method == 'GET':
        form = UpdateUserForm()
        if session['username'] == 'root':
            uid_username_list, default_id = getUsername2SelectForm()
        else:
            uid_username_list, default_id = getUsername2SelectForm('root')
        form.user_list.choices = uid_username_list
        form.user_list.default = default_id
        return render_template('updateuser.html', title=u'更新用户', username=session['username'],
                               page_header=u'更新用户', form=form), 200
    elif request.method == 'POST':
        form = UpdateUserForm()

        user_id = form.user_list.data
        username = form.username.data
        password = form.password.data
        password1 = form.password1.data
        password2 = form.password2.data
        if session['username'] == 'root':
            user = User.query.filter_by(uid=user_id).first()
        else:
            user = User.query.filter_by(uid=user_id, password=encrypt_password(password)).first()
        if user:
            # 相同用户名不用更改
            if username == user.username:
                username = ''
            # 不改用户名
            if not username:
                if password1 == password2:  # 密码一致验证
                    if password1:  # 密码非空，更新密码
                        if session['username'] != 'root' and user.username == 'root':
                            flash(u'非法操作')
                        else:
                            user.password = encrypt_password(password1)
                            flash(u'*已更新用户密码')
                    db.session.commit()
                else:
                    flash(u'密码前后不一致')
            # 更改用户名
            elif username and username != user.username:
                another_user = User.query.filter_by(username=username).first()
                if another_user:
                    flash(u'用户名 '+username+' 已存在')
                else:
                    if password1 == password2:
                        if password1:
                            user.password = encrypt_password(password1)
                            flash(u'*已更新用户密码')
                        if user.username == 'root':
                            flash(u'root用户名不能被更改')
                        else:
                            if update_user_dir(user.username, username, UPLOAD_FOLDER):
                                if session['username'] == user.username:
                                    session['username'] = username
                                user.username = username
                                flash(u'*已更新用户名')
                            else:
                                flash(u'无法更新用户名和用户文件夹')
                        db.session.commit()
                    else:
                        flash(u'密码前后不一致')
            else:
                flash(u'错误的输入')
        else:
            flash(u'错误的输入')
        form.username.data = ''
        if session['username'] == 'root':
            uid_username_list, default_id = getUsername2SelectForm()
        else:
            uid_username_list, default_id = getUsername2SelectForm('root')
        form.user_list.choices = uid_username_list
        form.user_list.default = default_id
        return render_template('updateuser.html', title=u'更新用户', username=session['username'],
                               page_header=u'更新用户', form=form), 200
    else:
        abort(404)


# 删除用户控制器
@app.route('/deluser', methods=['GET', 'POST'])
def deluser():
    if not validate_user(): return redirect('/login')
    if request.method == 'GET':
        form = DeleteUserForm()
        if session['username'] == 'root':
            uid_username_list, default_id = getUsername2SelectForm()
        else:
            uid_username_list, default_id = getUsername2SelectForm('root')
        form.user_list.choices = uid_username_list
        form.user_list.default = default_id
        return render_template('deluser.html', title=u'删除用户', username=session['username'],
                               page_header=u'删除一个或多个用户', form=form), 200
    elif request.method == 'POST':
        form = DeleteUserForm()
        if session['username'] == 'root':
            uid_username_list, default_id = getUsername2SelectForm()
        else:
            uid_username_list, default_id = getUsername2SelectForm('root')
        form.user_list.choices = uid_username_list
        form.user_list.default = default_id
        if form.validate_on_submit():
            uid = form.user_list.data
            password = form.password.data

            if session['username'] == 'root':
                user = User.query.filter_by(uid=uid).first()
            else:
                user = User.query.filter_by(uid=uid, password=encrypt_password(password)).first()
            if user:
                if (user.username) == 'root':
                    flash(u'权限不足， 无法删除 root')
                else:
                    del_flag = delete_user_dir(user.username, UPLOAD_FOLDER)
                    if del_flag:
                        db.session.delete(user)
                        flash(u'*已删除用户 '+(user.username))
                        links = Link.query.filter_by(username=user.username).all()
                        for link in links:
                            db.session.delete(link)
                        if (user.username) == session['username']:
                            session['username'] = ''
                    else:
                        flash(u'删除用户 ' + user.username + u'文件夹失败')
            else:
                flash(u'错误的输入')
            db.session.commit()
        else:
            flash(u'要删除的用户必须选择')
        if not validate_user(): return redirect('/login')
        if session['username'] == 'root':
            uid_username_list, default_id = getUsername2SelectForm()
        else:
            uid_username_list, default_id = getUsername2SelectForm('root')
        form.user_list.choices = uid_username_list
        form.user_list.default = default_id
        return render_template('deluser.html', title=u'删除用户', username=session['username'],
                               page_header=u'删除一个或多个用户', form=form), 200
    else:
        abort(404)


# 显示监控控制器
@app.route('/monitors')
def monitors():
    if not validate_user(): return redirect('/login')

    monitors = Monitor.query.all()
    response_html = ''
    collapse_head = '<br><div class="panel-group" id="accordion">'
    collapse_foot = '</div>'

    all_message_num = 0

    for monitor in monitors:
        mon_type = monitor.type
        mon_url = monitor.url
        mon_user = monitor.username
        mon_pass = monitor.password

        map_status_css = {
            'CRITICAL': 'danger',
            'WARNING': 'warning',
            'UNKNOWN': 'active',
            'DOWN': 'danger',
            '1': 'warning',
            '2': 'danger'
        }
        if judge_url_connect(mon_url):
            if mon_type == 'nagios':
                srv_table_tp, srv_tr_tp, host_table_tp, host_tr_tp = get_nagios_tmplate()
                try:
                    datas = login_nagios.login_nagios(mon_url, mon_user, mon_pass)
                except:
                    datas = {'service': [], 'host': []}
                    flash(u'用户名/密码/网络 存在问题, 无法连接至 '+monitor.aliname)
            elif mon_type == 'nagios3':
                srv_table_tp, srv_tr_tp, host_table_tp, host_tr_tp = get_nagios_tmplate()
                try:
                    datas = login_nagios3.login_nagios3(mon_url, mon_user, mon_pass)
                except:
                    datas = {'service': [], 'host': []}
                    flash(u'用户名/密码/网络 存在问题, 无法连接至 '+monitor.aliname)
            elif mon_type == 'centreon':
                srv_table_tp, srv_tr_tp, host_table_tp, host_tr_tp = get_nagios_tmplate()
                try:
                    datas = login_centron.login_centron(mon_url, mon_user, mon_pass)
                except:
                    datas = {'service': [], 'host': []}
                    flash(u'用户名/密码/网络 存在问题, 无法连接至 ' + monitor.aliname)
            else:
                srv_table_tp, srv_tr_tp, host_table_tp, host_tr_tp = get_cati_tmplate()
                try:
                    datas = login_cati.login_cati(mon_url, mon_user, mon_pass)
                except:
                    datas = {'service': [], 'host': []}
                    flash(u'用户名/密码/网络 存在问题, 无法连接至 ' + monitor.aliname)
        else:
            srv_table_tp, srv_tr_tp, host_table_tp, host_tr_tp = get_cati_tmplate()
            datas = {'service': [], 'host': []}
            flash(u'用户名/密码/网络 存在问题, 无法连接至 ' + monitor.aliname)

        num = 0
        srv_tbody_html = ''
        # print datas['service']
        for service in datas['service']:
            num += 1
            if service[2] in map_status_css:
                status_css = map_status_css[service[2]]
            else:
                status_css = 'success'
            data_tuple = (status_css,)+service
            srv_tbody_html += srv_tr_tp % data_tuple

        host_tbody_html = ''
        for host in datas['host']:
            num += 1
            if host[1] in map_status_css:
                status_css = map_status_css[host[1]]
            else:
                status_css = 'success'
            data_tuple = (status_css,) + host
            host_tbody_html += host_tr_tp % data_tuple

        all_message_num += num

        srv_table_html = srv_table_tp % (monitor.id, mon_url, monitor.aliname, srv_tbody_html)
        host_table_html = host_table_tp % (monitor.id, mon_url, monitor.aliname, host_tbody_html)

        table_html = host_table_html + srv_table_html
        collapse_tp = get_collapse_tp()  # id,aliname,num,id,<table>
        collapse_html = collapse_tp % (monitor.id, monitor.aliname, num, monitor.id, table_html)
        response_html += collapse_html

    # if response_html == '':
    #     response_html = '<p>暂无监控</p>'
    response_html = collapse_head + response_html + collapse_foot
    tables = Markup(response_html)

    if 'alarm' not in session:
        session['alarm'] = 1
    set_alarm = session['alarm']

    return render_template('monitors.html', title=u'监控 | 查看警报', username=session['username'], page_header=u'查看警报',
                           tables=tables, all_message_num=all_message_num, set_alarm=set_alarm), 200


# 增加监控控制器
@app.route('/addmon', methods=['POST'])
def addmon():
    if not validate_user(): return redirect('/login')
    form = AddMonitorForm()
    if form.validate_on_submit():
        url = request.form['mon_url']
        aliname = request.form['mon_aliname']
        user = request.form['mon_username']
        password = request.form['mon_password']
        mon_type = request.form['mon_type']
        # 检查连通性
        if mon_type == 'nagios':
            connected = login_nagios.test_nagios(url, user, password)
        elif mon_type == 'nagios3':
            connected = login_nagios3.test_nagios3(url, user, password)
        elif mon_type == 'centreon':
            connected = login_centron.test_centron(url, user, password)
        else:
            connected = login_cati.test_cati(url, user, password)
        if connected:
            mon = Monitor(url=url, aliname=aliname, username=user, password=password, type=mon_type)
            db.session.add(mon)
            db.session.commit()
            flash(u'*成功增加监控 '+aliname)
        else:
            flash(u'用户名/密码/网络 错误')
    else:
        flash(u'监控参数个数错误')
    return redirect('/monitors')


# 删除监控控制器
@app.route('/delmon', methods=['POST'])
def delmon():
    if not validate_user(): return redirect('/login')
    delmonform = DeleteMonitorForm()
    data_list, default_id, id_url_aliname = getMonitor2SelectField()
    delmonform.mon_list.choices = data_list
    delmonform.mon_list.default = default_id
    if delmonform.validate_on_submit():
        select_ids = delmonform.mon_list.data
        for select_id in select_ids:
            mon = Monitor.query.filter_by(id=select_id).first()
            if mon:
                db.session.delete(mon)
            flash(u'*成功删除 ' + mon.aliname)
        db.session.commit()
    else:
        flash(u'要删除的监控必须选择')
    return redirect('/monitors')


# 更新监控控制器
@app.route('/updatemon', methods=['POST'])
def updatemon():
    if not validate_user(): return redirect('/login')
    update_form = UpdateMonitorForm()
    data_list, default_id, id_url_aliname = getMonitor2SelectField()
    update_form.upmon_list.choices = data_list
    update_form.upmon_list.default = ''
    # update_form.update_url.data = id_url_desc[0][0]
    # update_form.update_desc.data = tranUnicode2Utf(id_url_desc[0][1])
    if update_form.validate_on_submit():
        update_id = update_form.upmon_list.data
        update_url = update_form.upmon_url.data
        update_aliname = update_form.upmon_aliname.data
        update_username = update_form.upmon_username.data
        update_password = update_form.upmon_password.data
        update_type = update_form.upmon_type.data

        mon = Monitor.query.filter_by(id=update_id).first()
        if mon:
            if update_url:
                if update_url != mon.url:
                    mon.url = update_url
            if update_aliname:
                if update_aliname != mon.aliname:
                    mon.aliname = update_aliname
            if update_username:
                if update_username != mon.username:
                    mon.username = update_username
            if update_password:
                if update_password != mon.password:
                    mon.password = update_password
            if update_type:
                if update_type != mon.type:
                    mon.type = update_type
            db.session.commit()
            flash(u'*成功修改监控 '+mon.aliname)
        else:
            flash(u'错误输入')
    else:
        flash(u'内容不能为空')
    return redirect('/monitors')


@app.route('/opmonitors', methods=['GET'])
def showopmon():
    if not validate_user(): return redirect('/login')
    update_form = UpdateMonitorForm()
    data_list, default_id, id_url_aliname = getMonitor2SelectField()
    update_form.upmon_list.choices = data_list
    update_form.upmon_list.default = default_id
    addmonform = AddMonitorForm()
    delmonform = DeleteMonitorForm()
    data_list, default_id, id_url_aliname = getMonitor2SelectField()
    delmonform.mon_list.choices = data_list
    delmonform.mon_list.default = default_id

    if len(data_list) > 0:
        show_del_update = True
    else:
        show_del_update = False

    return render_template('opmonitors.html', title=u'监控 | 相关操作', username=session['username'], page_header=u'相关操作',
                           updatemonform=update_form, addmonform=addmonform, delmon_form=delmonform,
                           show_del_update=show_del_update), 200


@app.route('/setalarm', methods=['POST'])
def setalarm():
    if not validate_user(): return redirect('/login')
    session['alarm'] = -session['alarm']
    return redirect('/monitors')


if __name__ == '__main__':
    # app.run(host="192.168.1.1", port=8080)
    app.run()
