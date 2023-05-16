# -*- coding: utf-8 -*-

import contextlib
import datetime
import functools
import logging
import os
import os.path as osp
from termcolor import colored
import time


def d_print(text):
    print(colored(text, 'cyan'))

def d_print_r(text):
    print(colored(text, 'red'))

def d_print_g(text):
    print(colored(text, 'green'))

def d_print_b(text):
    print(colored(text, 'blue'))

def d_print_y(text):
    print(colored(text, 'yellow'))


def get_name(path):
    name, _ = osp.splitext(osp.basename(path))
    return name


def setup_log(filename):
    """
    LogRecord attributes
        https://docs.python.org/3/library/logging.html#logrecord-attributes
    """
    medium_format = (
        '[%(asctime)s] %(levelname)s : %(filename)s[%(lineno)d] %(funcName)s'
        ' >>> %(message)s'
    )
    '''
    medium_format = (
        '[%(asctime)s] %(levelname)s : %(module)s > %(filename)s[%(lineno)d] %(funcName)s'
        ' >>> %(message)s'
    )
    '''
    if not filename.lower().endswith('.log'):
        filename = filename + '.log'
    log_dir = osp.abspath(osp.join(osp.dirname(__file__), '../logs'))
    if not osp.exists(log_dir):
        os.makedirs(log_dir)

    dt_now = datetime.datetime.now()
    get_log_file = osp.join(log_dir, filename)
    logging.basicConfig(
        filename=get_log_file,
        filemode='w',
        level=logging.INFO,
        format=medium_format
    )
    logging.info(f'@{get_log_file!r} created at {dt_now}')
    print(colored(f'@{get_log_file!r} created at {dt_now}', 'magenta'))


def itti_timer(func):
    """Print the runtime of the decorated function
    https://github.com/realpython/materials/blob/master/primer-on-python-decorators/decorators.py#L27
    """

    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        # print(f"Finished {func.__name__!r} in {run_time:.4f} secs")
        logging.info(f"Finished {func.__name__!r}(..) in {run_time:.4f} secs")
        return value

    return wrapper_timer


def itti_debug(func):
    """Print the function signature and return value
    https://github.com/realpython/materials/blob/master/primer-on-python-decorators/decorators.py#L42
    """

    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        # print(f"Calling {func.__name__}({signature})")
        logging.info(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        # print(f"{func.__name__!r} returned {value!r}")
        logging.info(f"{func.__name__!r} returned {value!r}")
        return value

    return wrapper_debug


class Profile(contextlib.ContextDecorator):
    """
    YOLOv8 Profile class.
    Usage: as a decorator with @Profile() or as a context manager with 'with Profile():'
    """

    def __init__(self, name="unknown", t=0.0):
        """
        Initialize the Profile class.

        Args:
            t (float): Initial time. Defaults to 0.0.
        """
        logging.info(f'Profile::__init__( {name}, {t} )')
        self.name = name
        self.t = t

    def __enter__(self):
        """
        Start timing.
        """
        self.start = self.time()
        return self

    def __exit__(self, type, value, traceback):
        """
        Stop timing.
        """
        self.dt = self.time() - self.start  # delta-time
        self.t += self.dt  # accumulate dt

    def time(self):
        """
        Get current time.
        """
        return time.time()
