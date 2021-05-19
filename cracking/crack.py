from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from cracking import db_util
from cracking import hash_util
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
        columns = ('id', 'hash', 'type', 'state', 'raw', 'created', 'updated')
        rows = db_util.get_tasks()
        for row in rows:
            tasks.append(dict(zip(columns, row)))
        return jsonify(tasks)
    else:
        return render_template('index.html')


@bp.route('/crack', methods=['GET', 'POST'])
def crack():
    """
    破解 MD5 或 SHA1
    """
    print("crack()")
    if request.method == 'POST':
        hash_data = request.form['hash_data']
        type = request.form['type'].strip()

        if not hash_data:
            abort(400)

        hash_data = hash_data.strip()
        hash_list = hash_data.split(',')
        for hash in hash_list:
            hash = hash.strip()
            if type == '0':
                print("MD5: " + hash)
            elif type == '1':
                print("SHA1: " + hash)
            else:
                pass

            task = db_util.get_task_by_hash(hash)
            if task is not None:
                if task['state'] == 3:
                    # 任务的状态为已取消，重新破解
                    db_util.set_task(task['id'], 0)  # 把任务的状态设为排队中
                elif task['state'] == 2:
                    # 任务的状态为已完成，返回原始密码
                    return {
                        "raw": task['raw']
                    }
                else:
                    pass
            else:
                db_util.create_task(hash, int(type))  # 在数据库中添加一个任务

        ray_util.start()  # 任务添加完毕，开始破解
        print('ray_util.start()')
        return redirect(url_for('index'))
    else:
        return render_template('index.html')


@bp.route('/stop_task', methods=['GET', 'POST'])
def stop_task():
    """
    停止任务
    """
    print("stop_task()")
    if request.method == 'POST':
        id = request.form['id']
        task = db_util.get_task(id)

        if task is None:
            abort(400)

        ray_util.stop_task(id)
        return redirect(url_for('index'))
    else:
        return render_template('index.html')


@bp.route('/get_progress')
def get_progress():
    """
    获取任务执行的进度
    """
    print("get_progress()")
    progress = ray_util.progress()
    print(progress)
    return {
        "progress": progress
    }


@bp.route('/generate', methods=['POST', 'GET'])
def generate():
    """
    生成 MD5 或 SHA1
    """
    print("generate()")
    if request.method == 'POST':
        raw = request.form['raw']
        type = request.form['type'].strip()

        if not raw:
            abort(400)

        raw = raw.strip()
        print(raw)
        if type == '0':
            print('MD5')
        elif type == '1':
            print('SHA1')
        else:
            pass

        type = int(type)
        if type == 0:
            hash = hash_util.generate_md5(raw)
        elif type == 1:
            hash = hash_util.generate_sha1(raw)
        else:
            pass

        return {
            "hash": hash
        }
    else:
        return render_template('generate.html')
