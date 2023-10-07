# -*- coding: utf-8 -*-

import os
import os.path as osp

__all__ = ['WorkSpace']

class WorkSpace:
    def __init__(self):
        self.this = osp.dirname(__file__)
        self.home = osp.abspath(osp.join(self.this, '..'))
        self.temp = osp.join(self.home, 'temp')
 
    def get_temp_dir(self):
        if not osp.exists(self.temp):
            os.makedirs(self.temp)
        return self.temp

    def get_save_dir(self, py_file):
        name, _ = osp.splitext(osp.basename(py_file))
        save_dir = osp.join(self.get_temp_dir(), name)
        if not osp.exists(save_dir):
            os.makedirs(save_dir)
        return save_dir
