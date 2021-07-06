import ray
from ray.exceptions import TaskCancelledError

from datetime import datetime
from datetime import timezone
from itertools import product

from cracking import db_util
from cracking import hash_util


# 原始密码每一位可能的取值
# chars = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
# chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
chars = '0123456789abcdefghijklmnopqrstuvwxyz'


class Queue():
    """
    队列
    """

    def __init__(self):
        """初始化 queue"""
        self.queue = []

    def enqueue(self, item):
        """入队"""
        self.queue.append(item)

    def enqueue_list(self, items):
        """列表入队"""
        self.queue.extend(items)

    def dequeue(self):
        """出队"""
        return self.queue.pop(0)

    def remove(self, item):
        """删除某个元素"""
        self.queue.remove(item)

    def is_empty(self):
        """队列是否为空"""
        return len(self.queue) == 0

    def size(self):
        """队列的长度"""
        return len(self.queue)

    def iterator(self):
        """迭代器"""
        return self.queue


task_queue = Queue()  # 等待执行的任务队列，元素的数据类型为 <class 'sqlite3.Row'>
is_started = False  # 是否开始计算
result_ids = []  # Ray 未执行的计算任务
is_canceled = False  # 用户是否取消任务
last_time = None  # 最近一次添加到任务队列的时间


@ray.remote
def crack_md5(md5, head, start=4, end=32):
    """
    破解 MD5

    :param md5: 待破解的 MD5
    :param head: 首部字符
    :param start: 原始密码长度，最短位数
    :param end: 原始密码长度，最长位数
    :return: 原始密码。如果破解失败，返回 None
    """
    try:
        for length in range(start, end):
            for char_list in product(chars, repeat=length - len(head)):
                string = ''.join(char_list)
                raw = head + string
                if hash_util.generate_md5(raw) == md5:
                    return raw
    except TaskCancelledError:
        print("Object reference was cancelled.")
        return None
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        return None
    return None


@ray.remote
def crack_sha1(sha1, head, start=4, end=32):
    """
    破解 SHA1

    :param sha1: 待破解的 SHA1
    :param head: 首部字符
    :param start: 原始密码长度，最短位数
    :param end: 原始密码长度，最长位数
    :return: 原始密码。如果破解失败，返回 None
    """
    try:
        for length in range(start, end):
            for char_list in product(chars, repeat=length - len(head)):
                string = ''.join(char_list)
                raw = head + string
                if hash_util.generate_sha1(raw) == sha1:
                    return raw
    except TaskCancelledError:
        print("Object reference was cancelled.")
        return None
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        return None
    return None


def start():
    """
    开始破解
    """
    print("start()")
    global task_queue
    global is_started
    global last_time

    if is_started:
        # 正在破解，把新任务添加到 task_queue
        tasks = db_util.get_queue_tasks_by_updated(last_time)
        last_time = datetime.now(timezone.utc)  # SQLite 3 中存储的是 UTC 时间，因此这里为 UTC 时间
        task_queue.enqueue_list(tasks)
        return

    is_started = True

    # 解决上一次运行中的任务突然停止的情况
    tasks = db_util.get_running_tasks()
    for task in tasks:
        db_util.set_task(task['id'], 0)  # 把运行中任务改为排队中任务

    tasks = db_util.get_queue_tasks()  # 所有排队中的任务
    task_queue.enqueue_list(tasks)  # 添加到任务队列
    last_time = datetime.now(timezone.utc)  # SQLite 3 中存储的是 UTC 时间，因此这里为 UTC 时间
    while not task_queue.is_empty():
        task = task_queue.dequeue()
        id = task['id']
        hash = task['hash']
        type = task['type']
        db_util.set_task(id, 1)  # 把状态设为运行中
        raw = distribute_computation(hash, type)
        if raw is None:
            # 用户取消任务，把状态设为已取消
            db_util.set_task(id, 3)
        elif raw == '':
            # 破解失败，把状态设为未破解
            db_util.set_task(id, 4)
        else:
            # 破解成功，把状态设为已完成，把原始密码存到数据库中
            db_util.set_task(id, 2, raw)

    is_started = False


def stop_task(id):
    """
    停止任务

    :param id: ID
    """
    global task_queue
    global is_started

    if not is_started:
        # Ray 未开始计算或计算完成，直接返回
        return

    if isinstance(id, str):
        id = int(id)
    for task in task_queue.iterator():
        if task['id'] == id:
            # 如果要停止的任务在任务队列中，则在任务队列中删除该任务
            task_queue.remove(task)
            db_util.set_task(task['id'], 3)  # 把任务状态设为已取消
            return
    # 要停止的任务为当前执行的任务，则停止计算
    stop_computation()


def distribute_computation(hash, type):
    """
    分发计算任务，即分布式计算

    :param id: ID
    :param hash: 待破解的哈希值
    :param type: 哈希值的类型
    :return: 原始密码
    """
    print('distribute_computation()')
    global result_ids
    global is_canceled

    if type == 0:
        result_ids = [crack_md5.remote(hash, c1 + c2, 4, 6) for c1 in chars for c2 in chars]
    elif type == 1:
        result_ids = [crack_sha1.remote(hash, c1 + c2, 4, 6) for c1 in chars for c2 in chars]
    else:
        pass

    raw = ''
    while len(result_ids):
        if is_canceled:
            # 用户停止任务，直接返回
            return None

        # print("distribute_computation() -> before ray.wait() -> len(result_ids) = {0}".format(len(result_ids)))
        done_id, result_ids = ray.wait(result_ids, num_returns=1, timeout=None)
        # print("distribute_computation() -> after ray.wait() -> len(result_ids) = {0}".format(len(result_ids)))
        try:
            raw = ray.get(done_id[0])  # 获取破解结果
        except TaskCancelledError:
            print("Object reference was cancelled.")
            return None
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            return None
        if raw is not None and raw != '':
            # 破解成功，停止其他节点的计算任务
            stop_computation()
            break
        else:
            pass

    return raw


def stop_computation():
    """
    停止 Ray 节点的计算任务
    """
    print('stop_computation()')
    global result_ids
    global is_canceled

    is_canceled = True
    for result_id in result_ids:
        ray.cancel(result_id, force=True)
    result_ids = []
    is_canceled = False


def progress():
    """
    任务执行的进度
    """
    global is_started
    global result_ids

    if is_started:
        # 破解一个 hash 分配 len(chars) * len(chars) 个计算任务
        return 1 - len(result_ids) / (len(chars) * len(chars))
    else:
        return -1
