#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import logging
import stat
import errno
import time
import fuse


class Memory(fuse.LogInfo, fuse.Operations):
    def __init__(self):
        super().__init__()  # 初始化日志类
        self.files = {}
        self.data = collections.defaultdict(bytes)
        self.fd = 0
        now = time.time()
        self.files['/'] = dict(
            st_mode=(stat.S_IFDIR | 0o755),
            st_ctime=now,
            st_mtime=now,
            st_atime=now,
            st_nlink=2)

    def mkdir(self, path, mode):
        # now = time.time()
        self.files[path] = dict(
            st_mode=(stat.S_IFDIR | mode),
            st_nlink=2,
            st_size=0,
            st_ctime=time.time(),
            st_mtime=time.time(),
            st_atime=time.time()
        )
        self.files['/']['st_nlink'] += 1

    def chmod(self, path, mode):
        # 补充
        self.files[path]['st_mode'] &= 0o770000
        self.files[path]['st_mode'] |= mode
        return 0

    def chown(self, path, uid, gid):
        self.files[path]['st_uid'] = uid
        self.files[path]['st_gid'] = gid

    def rmdir(self, path):
        del self.files[path]
        self.files['/']['st_nlink'] -= 1

    def create(self, path, mode):
        # now = time.time()
        self.files[path] = dict(
            st_mode=(stat.S_IFREG | mode),
            st_nlink=1,
            st_size=0,
            st_ctime=time.time(),
            st_mtime=time.time(),
            st_atime=time.time()
        )
        self.fd += 1
        return self.fd

    def open(self, path, mode):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        return self.data[path][offset: offset+size]

    def readdir(self, path, fh):
        ret = ['.', '..'] + [file[1:] for file in self.files if file != '/']
        return ret

    def readlink(self, path, size):
        return self.data[path]

    def getattr(self, path, fh=None):
        print("\n\nLook --> "+path)
        if path not in self.files:
            raise fuse.FuseOSError(errno.ENOENT)

        return self.files[path]

    # 拓展属性的支持
    def getxattr(self, path, name, position=0):
        attrs = self.files[path].get('attrs', {})
        try:
            return attrs[name]
        except KeyError:
            return ''       # Should return ENOATTR

    def listxattr(self, path):
        attrs = self.files[path].get('attrs', {})
        return attrs.keys()

    def rename(self, old_name, new_name):
        self.data[new_name] = self.data.pop(old_name)
        self.files[new_name] = self.files.pop(old_name)

    def write(self, path, data, offset, fh):
        self.data[path] = (
            self.data[path][:offset].ljust(offset, '\x00'.encode('ascii'))
            + data
            + self.data[path][offset+len(data):]
        )
        self.files[path]['st_size'] = len(self.data[path])
        return len(data)

    def setxattr(self, path, name, value, options, position=0):
        # 部分选项保留
        attrs = self.files[path].setdefault('attrs', {})
        attrs[name] = value

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        self.files[target] = dict(
            st_mode=(stat.S_IFLNK | 0o777),
            st_nlink=1,
            st_size=len(source))

        self.data[target] = source

    def truncate(self, path, length, fh=None):
        # 拓展文件用0x00填充
        self.data[path] = self.data[path][:length].ljust(
            length, '\x00'.encode('ascii'))
        self.files[path]['st_size'] = length

    def unlink(self, path):
        self.data.pop(path)
        self.files.pop(path)

    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        self.files[path]['st_atime'] = atime
        self.files[path]['st_mtime'] = mtime


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('mount')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    fuseObj = fuse.Fuse(Memory(), args.mount,
                        foreground=False, allow_other=True)
