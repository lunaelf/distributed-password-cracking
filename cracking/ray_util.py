import ray
from ray.exceptions import TaskCancelledError

from itertools import permutations

from cracking import md5_util


ray.init()
# ray.init(address='auto', _redis_password='5241590000000000')
# chars = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
# chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
chars = '0123456789abcdefghijklmnopqrstuvwxyz'

# result_ids 和 is_cancel 用来协调 distribute_task 方法 和 cancel_task 方法的执行
result_ids = []
is_cancel = False


@ray.remote
def crack_md5_(md5, head, start=4, end=32):
    """
    破解 MD5

    :param md5: 待破解的 MD5
    :param head: 第一个字符
    :param start: 密码长度，最短位数
    :param end: 密码长度，最长位数
    :return: 原始密码。如果没有破解成功，返回 None
    """
    for length in range(start, end):
        for char_list in permutations(chars, length - len(head)):
            string = ''.join(char_list)
            password = head + string
            if md5_util.generate(password) == md5:
                return password
    return None

def distribute_task(md5):
    """
    分发任务

    :param md5: 待破解的 MD5
    :return: 原始密码
    """
    global result_ids
    global is_cancel

    # result_ids = [crack_md5_.remote(md5, c1 + c2, 4, 20) for c1 in chars for c2 in chars]
    result_ids = [crack_md5_.remote(md5, c1 + c2, 4, 6) for c1 in chars for c2 in chars]
    result = None
    while len(result_ids):
        done_id, result_ids = ray.wait(result_ids, num_returns=1, timeout=None)
        if is_cancel:
            # 用户停止任务，直接返回
            return None
        try:
            result = ray.get(done_id[0])  # 获取解密结果
        except TaskCancelledError:
            print("Object reference was cancelled.")
            return None
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            return None
        if result is not None:
            # MD5 破解完成，跳转到 cancel_task()，停止其他节点的计算任务
            break

    cancel_task()
    return result


def cancel_task():
    """
    取消任务
    """
    global result_ids
    global is_cancel

    is_cancel = True
    for result_id in result_ids:
        ray.cancel(result_id)
    result_ids = []
    is_cancel = False


def get_progress():
    """
    获取任务执行的进度
    """
    # result_ids 表示未执行的任务
    if len(result_ids) != 0:
        # 总共分配 len(chars) * len(chars) 个任务
        return 1 - len(result_ids) / (len(chars) * len(chars))
    else:
        return -1
