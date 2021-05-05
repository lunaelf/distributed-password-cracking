from datetime import datetime

from cracking.db import get_db


def get_task(password):
    """
    根据密码（MD5）获取任务信息

    :param password: 密码（MD5）
    :return: 一个任务信息。如果没找到，返回 None
    """
    task = get_db().execute(
        'SELECT id, password, state, result, created, updated'
        ' FROM task'
        ' WHERE password = ?',
        (password,)
    ).fetchone()

    return task


def set_task(password, state, result='', updated=str(datetime.now())):
    """
    更新任务信息

    :param password: 密码（MD5）
    :param state: 任务的状态，{0: 进行中, 1: 已完成, 2: 已取消}
    :param result: 解密结果
    :param updated: 更新时间
    """
    db = get_db()
    db.execute(
        'UPDATE task SET state = ?, result = ?, updated = ?'
        ' WHERE password = ?',
        (state, result, updated, password)
    )
    db.commit()


def get_all_task():
    """
    获取所有的任务信息

    :return: 所有的任务信息
    """
    tasks = get_db().execute(
        'SELECT id, password, state, result, created, updated'
        ' FROM task'
        ' ORDER BY created DESC'
    ).fetchall()

    return tasks


def create_task(password, state, result=''):
    """
    插入一条任务

    :param password: 密码（MD5）
    :param state: 任务的状态，{0: 进行中, 1: 已完成, 2: 已取消}
    :param result: 解密结果
    """
    db = get_db()
    db.execute(
        'INSERT INTO task (password, state, result)'
        ' VALUES (?, ?, ?)',
        (password, state, result)
    )
    db.commit()


def delete_task(password):
    """
    根据密码（MD5）删除任务信息

    :param password: 密码（MD5）
    """
    db = get_db()
    db.execute(
        'DELETE FROM task'
        ' WHERE password = ?',
        (password,)
    )
    db.commit()
