from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from cracking import db_util
from cracking import md5_util
from cracking import ray_util


bp = Blueprint('crack', __name__)


@bp.route('/', methods=['GET', 'POST'])
def index():
    """
    首页
    """
    print("index()")
    if request.method == 'POST':
        tasks = []
        columns = ['id', 'password', 'state', 'result', 'created', 'updated']
        rows = db_util.get_all_task()
        for row in rows:
            tasks.append(dict(zip(columns, row)))
        return jsonify(tasks)
    else:
        return render_template('index.html')


@bp.route('/crack', methods=['GET', 'POST'])
def crack():
    """
    破解 MD5
    """
    print("crack()")
    if request.method == 'POST':
        md5_data = request.form['md5_data']
        md5_data = md5_data.strip()
        error = None

        if not md5_data:
            error = '密码（MD5）不能为空。'

        if error is not None:
            # flash(error)
            abort(400)

        md5_list = md5_data.split(',')
        for md5 in md5_list:
            md5 = md5.strip()
            print("MD5: " + md5)

            task = db_util.get_task(md5)
            if task is not None:
                state = task["state"]
                if state == 1:
                    # 状态为已完成，该 MD5 已经破解过了，直接返回
                    return redirect(url_for('index'))
                else:
                    # 状态为进行中或已取消，重新执行任务
                    db_util.set_task(md5, 0)
                    result = ray_util.distribute_task(md5)
                    if result is not None:
                        # 更新数据库中的任务
                        db_util.set_task(md5, 1, result)
                    else:
                        # 用户停止任务或破解失败
                        pass
            else:
                db_util.create_task(md5, 0)  # 在数据库中添加一个任务
                result = ray_util.distribute_task(md5)  # 分配任务，分布式解密
                if result is not None:
                    # 更新数据库中的任务
                    db_util.set_task(md5, 1, result)
                else:
                    # 用户停止任务或破解失败
                    pass
        return redirect(url_for('index'))
    else:
        render_template('index.html')


@bp.route('/stop_task', methods=['GET', 'POST'])
def stop_task():
    """
    停止任务
    """
    print("stop_task()")
    if request.method == 'POST':
        password = request.form['password']
        task = db_util.get_task(password)
        if task is not None:
            ray_util.cancel_task()
            db_util.set_task(password, 2)
            return redirect(url_for('index'))
        else:
            abort(400)
    else:
        render_template('index.html')


@bp.route('/get_progress')
def get_progress():
    """
    获取任务执行的进度
    """
    print("get_progress()")
    progress = ray_util.get_progress()
    print(progress)
    return {
        "progress": progress
    }


@bp.route('/generate', methods=['POST', 'GET'])
def generate():
    """
    生成 MD5
    """
    print("generate()")
    if request.method == 'POST':
        text = request.form['text']
        text = text.strip()
        print(text)
        md5 = md5_util.generate(text)
        return {
            "md5": md5
        }
    else:
        return render_template('generate.html')
