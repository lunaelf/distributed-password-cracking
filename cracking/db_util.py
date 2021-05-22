from datetime import datetime

from cracking.db import get_db


def get_tasks():
    """
    获取所有的任务信息

    :return: 所有的任务信息
    """
    tasks = get_db().execute(
        'SELECT id, hash, type, state, raw, created, updated'
        ' FROM task'
        ' WHERE deleted = 0'
        ' ORDER BY created DESC'
    ).fetchall()

    return tasks


def get_queue_tasks():
    """
    获取排队中的任务

    :return: 排队中的任务
    """
    tasks = get_db().execute(
        'SELECT id, hash, type, state, raw, created, updated'
        ' FROM task'
        ' WHERE state = 0 AND deleted = 0'
        ' ORDER BY created DESC'
    ).fetchall()

    return tasks


def get_queue_tasks_by_updated(updated):
    """
    获取某更新时间以后排队中的任务

    :param updated: 更新时间
    :return: 某更新时间以后排队中的任务
    """
    tasks = get_db().execute(
        'SELECT id, hash, type, state, raw, created, updated'
        ' FROM task'
        ' WHERE state = 0 AND updated > ? AND deleted = 0'
        ' ORDER BY created DESC',
        (str(updated),)
    ).fetchall()

    return tasks


def get_running_tasks():
    """
    获取运行中的任务

    :return: 运行中的任务
    """
    tasks = get_db().execute(
        'SELECT id, hash, type, state, raw, created, updated'
        ' FROM task'
        ' WHERE state = 1 AND deleted = 0'
        ' ORDER BY created DESC'
    ).fetchall()

    return tasks


def get_task(id):
    """
    根据 id 获取任务信息

    :param id: ID
    :return: 一个任务信息。如果没找到，返回 None
    """
    task = get_db().execute(
        'SELECT id, hash, type, state, raw, created, updated'
        ' FROM task'
        ' WHERE id = ? AND deleted = 0',
        (id,)
    ).fetchone()

    return task


def get_task_by_hash(hash):
    """
    根据 hash 获取任务信息

    :param hash: 原始密码的哈希值
    :return: 一个任务信息。如果没找到，返回 None
    """
    task = get_db().execute(
        'SELECT id, hash, type, state, raw, created, updated'
        ' FROM task'
        ' WHERE hash = ? AND deleted = 0',
        (hash,)
    ).fetchone()

    return task


def set_task(id, state, raw=''):
    """
    根据 ID 更新任务信息

    :param id: ID
    :param state: 任务的状态，{0: 排队中, 1: 运行中, 2: 已完成, 3: 已取消, 4: 未破解}
    :param raw: 原始密码
    """
    db = get_db()
    db.execute(
        'UPDATE task SET state = ?, raw = ?, updated = ?'
        ' WHERE id = ?',
        (state, raw, str(datetime.now()), id)
    )
    db.commit()


def create_task(hash, type=0):
    """
    插入一条任务

    :param hash: 原始密码的哈希值
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
