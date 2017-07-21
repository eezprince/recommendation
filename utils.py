import os


def ensure_folder_exists(path):

    if not os.path.exists(path):
        os.makedirs(path)


def replace_last(source_string, replace_what, replace_with):

    head, _sep, tail = source_string.rpartition(replace_what)
    return head + replace_with + tail
