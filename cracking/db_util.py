from datetime import datetime

from cracking.db import get_db


def get_task(id):
    """
    根据 id 获取任务信息

    :param id: ID
    :return: 一个任务信息。如果没找到，返回 None
    """
    task = get_db().execute(
        'SELECT id, hash, type, state, raw, created, updated, deleted'
        ' FROM task'
        ' WHERE id = ? AND deleted = 0',
        (id,)
    ).fetchone()

    return task


def set_task(id, state, raw=''):
    """
    根据 ID 更新任务信息

    :param id: ID
    :param state: 任务的状态，{0: 排队中, 1: 进行中, 2: 已完成, 3: 已取消}
    :param raw: 原文
    """
    db = get_db()
    db.execute(
        'UPDATE task SET state = ?, raw = ?, updated = ?'
        ' WHERE id = ?',
        (state, raw, str(datetime.now()), id)
    )
    db.commit()


def get_all_task():
    """
    获取所有的任务信息

    :return: 所有的任务信息
    """
    tasks = get_db().execute(
        'SELECT id, hash, type, state, raw, created, updated, deleted'
        ' FROM task'
        ' WHERE deleted = 0'
        ' ORDER BY created DESC'
    ).fetchall()

    return tasks


def create_task(hash, type=0):
    """
    插入一条任务

    :param hash: 密码的哈希值
    :param type: 哈希值的类型，{0: MD5, 1: SHA1}
    """
    db = get_db()
    db.execute(
        'INSERT INTO task (hash, type, state, raw)'
        ' VALUES (?, ?, 0, "")',
        (hash, type)
    )
    db.commit()


def delete_task(id):
    """
    根据 ID 删除任务信息，即把该任务的 deleted 设为 1。{0: 未删除, 1: 已删除}

    :param id: ID
    """
    db = get_db()
    db.execute(
        'UPDATE task SET deleted = ?'
        ' WHERE id = ?',
        (id)
    )
    db.commit()
