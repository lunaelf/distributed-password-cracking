import hashlib


def generate_md5(raw):
    """
    生成 MD5

    :param raw: 原始字符串
    :return: MD5
    """
    if isinstance(raw, str):
        return hashlib.md5(raw.encode('utf-8')).hexdigest()
    else:
        raise TypeError


def generate_sha1(raw):
    """
    生成 sha1

    :param raw: 原始字符串
    :return: SHA1
    """
    if isinstance(raw, str):
        return hashlib.sha1(raw.encode('utf-8')).hexdigest()
    else:
        raise TypeError
