from hashlib import md5


def generate(raw):
    """
    生成 MD5

    :param raw: 原始字符串
    :return: MD5
    """
    if isinstance(raw, str):
        return md5(raw.encode('utf-8')).hexdigest()
    else:
        raise TypeError
