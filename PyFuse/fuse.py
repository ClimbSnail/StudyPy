#!/usr/bin/env python
# -*- coding: utf-8 -*-

from signal import signal, SIGINT, SIG_DFL
from functools import partial
import base_struct as bs
import stat
import errno
import ctypes
import logging
import errno
import os

logger = logging.getLogger("fuse")


def time_of_timespec(ts, use_ns=False):
    if use_ns:
        return ts.tv_sec * 10 ** 9 + ts.tv_nsec
    else:
        return ts.tv_sec + ts.tv_nsec / 1E9


def set_st_attrs(st, attrs, use_ns=False):
    for key, val in attrs.items():
        if key in ('st_atime', 'st_mtime', 'st_ctime', 'st_birthtime'):
            timespec = getattr(st, key + 'spec', None)
            if timespec is None:
                continue

            if use_ns:
                timespec.tv_sec, timespec.tv_nsec = divmod(int(val), 10 ** 9)
            else:
                timespec.tv_sec = int(val)
                timespec.tv_nsec = int((val - timespec.tv_sec) * 1E9)
        elif hasattr(st, key):
            setattr(st, key, val)


def fuse_get_context():
    '返回 (uid, gid, pid) 元祖'

    ctxp = bs._libfuse.fuse_get_context()
    ctx = ctxp.contents
    return ctx.uid, ctx.gid, ctx.pid


class LogInfo(object):
    """
    所有的具体实现类都应该继承该日志接口
    """

    def __init__(self):
        """
        所有继承该类的具体类都应该初始化时显示调用 super.__init__()
        """
        self.logger = logging.getLogger(
            "fuse_for_"+self.__class__.__name__+".log")

    def __call__(self, op, path, *args):
        self.logger.debug('-> %s %s %s', op, path, repr(args))
        ret = '[Unhandled Exception]'
        try:
            ret = getattr(self, op)(path, *args)
            return ret
        except OSError as e:
            ret = str(e)
            raise
        finally:
            self.logger.debug('<- %s %s', op, repr(ret))


class FuseOSError(OSError):
    def __init__(self, errno):
        super(FuseOSError, self).__init__(errno, os.strerror(errno))


class Operations(object):
    """
    所有的具体实现类需要继承该操作类，
    以下是给定的操作接口，具体实现类n选m实现接口即可（n>=m）
    """

    def __call__(self, op, *args):
        if not hasattr(self, op):
            raise FuseOSError(errno.EFAULT)
        return getattr(self, op)(*args)

    def access(self, path, amode):
        return 0

    def mkdir(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def chmod(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def chown(self, path, uid_t, gid_t):
        raise FuseOSError(errno.EROFS)

    def rmdir(self, path):
        raise FuseOSError(errno.EROFS)

    def create(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def destroy(self, path):
        '在文件系统销毁时调用。路径始终为/'
        pass

    def flush(self, path, fh):
        return 0

    def fsync(self, path, datasync, fh):
        return 0

    def fsyncdir(self, path, datasync, fh):
        return 0

    def getattr(self, path, fh=None):

        if path != '/':
            raise FuseOSError(errno.ENOENT)
        return dict(st_mode=(stat.S_IFDIR | 0o755), st_nlink=2)

    def getxattr(self, path, name, position=0):
        raise FuseOSError(errno.ENOTSUP)

    def init(self, path):
        '''
        在文件系统初始化时调用。（路径始终为/）
        如果在初始化时启动线程，请使用它而不是__init__。
        '''
        pass

    def ioctl(self, path, cmd, arg, fip, flags, data):
        raise FuseOSError(errno.ENOTTY)

    def link(self, target, source):
        raise FuseOSError(errno.EROFS)

    def listxattr(self, path):
        return []

    def open(self, path, mode):
        # raise FuseOSError(errno.EROFS)

        return 0

    def opendir(self, path):
        # raise FuseOSError(errno.EROFS)

        return 0

    def read(self, path, mode, size, offset):
        raise FuseOSError(errno.EROFS)

    def readdir(self, path, fh):
        return ['.', '..']

    def readlink(self, path, size):
        raise FuseOSError(errno.EROFS)

    def release(self, path, fh):
        return 0

    def releasedir(self, path, fh):
        return 0

    def removexattr(self, path, name):
        raise FuseOSError(errno.ENOTSUP)

    def rename(self, old_name, new_name):
        raise FuseOSError(errno.EROFS)

    def setxattr(self, path, name, value, options, position=0):
        raise FuseOSError(errno.ENOTSUP)

    def statfs(self, path):
        return {}

    def symlink(self, target, source):
        raise FuseOSError(errno.EROFS)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(errno.EROFS)

    def unlink(self, path):
        raise FuseOSError(errno.EROFS)

    def utimens(self, path, times=None):
        'times是一个元祖(atime，mtime)，可以使用当前时间'
        return 0

    def write(self, path, data, offset):
        raise FuseOSError(errno.EROFS)


class FuseOperations(ctypes.Structure):
    """
    对应fuse.h里定义的接口(定义函数原型)
    """
    _fields_ = [
        ('getattr', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(bs.c_stat))),

        ('readlink', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_byte),
            ctypes.c_size_t)),

        ('getdir', ctypes.c_voidp),    # Deprecated, use readdir

        ('mknod', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, bs.c_mode_t, bs.c_dev_t)),

        ('mkdir', ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, bs.c_mode_t)),
        ('unlink', ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p)),
        ('rmdir', ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p)),

        ('symlink', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)),

        ('rename', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)),

        ('link', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)),

        ('chmod', ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, bs.c_mode_t)),

        ('chown', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, bs.c_uid_t, bs.c_gid_t)),

        ('truncate', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, bs.c_off_t)),

        ('utime', ctypes.c_voidp),     # Deprecated, use utimens
        ('open', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(bs.fuse_file_info))),

        ('read', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_byte),
            ctypes.c_size_t, bs.c_off_t, ctypes.POINTER(bs.fuse_file_info))),

        ('write', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_byte),
            ctypes.c_size_t, bs.c_off_t, ctypes.POINTER(bs.fuse_file_info))),

        ('statfs', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(bs.c_statvfs))),

        ('flush', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(bs.fuse_file_info))),

        ('release', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(bs.fuse_file_info))),

        ('fsync', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
            ctypes.POINTER(bs.fuse_file_info))),

        ('setxattr', bs.setxattr_t),
        ('getxattr', bs.getxattr_t),

        ('listxattr', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_byte),
            ctypes.c_size_t)),

        ('removexattr', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)),

        ('opendir', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(bs.fuse_file_info))),

        ('readdir', ctypes.CFUNCTYPE(
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_voidp,
            ctypes.CFUNCTYPE(
                ctypes.c_int, ctypes.c_voidp, ctypes.c_char_p,
                ctypes.POINTER(bs.c_stat), bs.c_off_t),
            bs.c_off_t,
            ctypes.POINTER(bs.fuse_file_info))),

        ('releasedir', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(bs.fuse_file_info))),

        ('fsyncdir', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
            ctypes.POINTER(bs.fuse_file_info))),

        ('init', ctypes.CFUNCTYPE(ctypes.c_voidp, ctypes.c_voidp)),
        ('destroy', ctypes.CFUNCTYPE(ctypes.c_voidp, ctypes.c_voidp)),

        ('access', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int)),

        ('create', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, bs.c_mode_t,
            ctypes.POINTER(bs.fuse_file_info))),

        ('ftruncate', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, bs.c_off_t,
            ctypes.POINTER(bs.fuse_file_info))),

        ('fgetattr', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(bs.c_stat),
            ctypes.POINTER(bs.fuse_file_info))),

        ('lock', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(bs.fuse_file_info),
            ctypes.c_int, ctypes.c_voidp)),

        ('utimens', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(bs.c_utimbuf))),

        ('bmap', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_ulonglong))),

        ('flag_nullpath_ok', ctypes.c_uint, 1),
        ('flag_nopath', ctypes.c_uint, 1),
        ('flag_utime_omit_ok', ctypes.c_uint, 1),
        ('flag_reserved', ctypes.c_uint, 29),

        ('ioctl', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_uint, ctypes.c_void_p,
            ctypes.POINTER(bs.fuse_file_info), ctypes.c_uint, ctypes.c_void_p)),
    ]


class Fuse(object):
    """
    Fuse Conctrller
    """
    __critical_exception = None

    OPTIONS = (
        ('foreground', '-f'),
        ('debug', '-d'),
        ('nothreads', '-s'),
    )

    def __init__(self, operations_obj, mount_point, encoding='utf-8', **kwargs):
        self.operations = operations_obj
        self.raw_fi = False
        self.use_ns = getattr(operations_obj, 'use_ns', False)
        self.encoding = encoding
        args = ['fuse']

        args.extend(flag for arg, flag in self.OPTIONS
                    if kwargs.pop(arg, False))

        kwargs.setdefault('fsname', operations_obj.__class__.__name__)
        args.append('-o')
        args.append(','.join(self._normalize_fuse_options(**kwargs)))
        args.append(mount_point)

        args = [arg.encode(encoding) for arg in args]
        argv = (ctypes.c_char_p * len(args))(*args)

        fuse_ops = FuseOperations()
        for ent in FuseOperations._fields_:
            name, prototype = ent[:2]

            check_name = name

            if check_name in ["ftruncate", "fgetattr"]:
                check_name = check_name[1:]

            val = getattr(operations_obj, check_name, None)
            if val is None:
                continue

            # 'argtypes'(参数格式)是ctypes.CFUNCTYPE类的一个属性
            if hasattr(prototype, 'argtypes'):
                val = prototype(partial(self._wrapper, getattr(self, name)))

            setattr(fuse_ops, name, val)

        try:
            old_handler = signal(SIGINT, SIG_DFL)
        except ValueError:
            old_handler = SIG_DFL

        err = bs._libfuse.fuse_main_real(
            len(args), argv, ctypes.pointer(fuse_ops),
            ctypes.sizeof(fuse_ops),
            None)

        try:
            signal(SIGINT, old_handler)
        except ValueError:
            pass

        del self.operations     # Invoke the destructor
        if Fuse.__critical_exception:
            raise Fuse.__critical_exception
        if err:
            raise RuntimeError(err)

    @staticmethod
    def _normalize_fuse_options(**kargs):
        for key, value in kargs.items():
            if isinstance(value, bool):
                if value is True:
                    yield key
            else:
                yield '%s=%s' % (key, value)

    @staticmethod
    def _wrapper(func, *args, **kwargs):
        '用于下面方法的修饰器'

        try:
            if func.__name__ == "init":
                return func(*args, **kwargs) or 0

            else:
                try:
                    return func(*args, **kwargs) or 0

                except OSError as e:
                    if e.errno > 0:
                        logger.debug(
                            "FUSE operation %s raised a %s, returning errno %s.",
                            func.__name__, type(e), e.errno, exc_info=True)
                        return -e.errno
                    else:
                        logger.error(
                            "FUSE operation %s raised an OSError with negative "
                            "errno %s, returning errno.EINVAL.",
                            func.__name__, e.errno, exc_info=True)
                        return -errno.EINVAL

                except Exception:
                    logger.error("Uncaught exception from FUSE operation %s, "
                                 "returning errno.EINVAL.",
                                 func.__name__, exc_info=True)
                    return -errno.EINVAL

        except BaseException as e:
            Fuse.__critical_exception = e
            logger.critical(
                "Uncaught critical exception from FUSE operation %s, aborting.",
                func.__name__, exc_info=True)
            # 异常捕获 退出系统
            fuse_ptr = ctypes.c_void_p(
                bs._libfuse.fuse_get_context().contents.fuse)
            bs._libfuse.fuse_exit(fuse_ptr)
            return -errno.EFAULT

    def _decode_optional_path(self, path):
        # NB: this method is intended for fuse operations that
        #     allow the path argument to be NULL,
        #     *not* as a generic path decoding method
        if path is None:
            return None
        return path.decode(self.encoding)

    def getattr(self, path, buf):
        return self.fgetattr(path, buf, None)

    def readlink(self, path, buf, bufsize):
        ret = self.operations('readlink', path.decode(self.encoding))\
            .encode(self.encoding)

        # 将字符串复制到给定缓冲区
        data = ctypes.create_string_buffer(ret[:bufsize - 1])
        ctypes.memmove(buf, data, len(data))
        return 0

    def mknod(self, path, mode, dev):
        return self.operations('mknod', path.decode(self.encoding), mode, dev)

    def mkdir(self, path, mode):
        return self.operations('mkdir', path.decode(self.encoding), mode)

    def unlink(self, path):
        return self.operations('unlink', path.decode(self.encoding))

    def rmdir(self, path):
        return self.operations('rmdir', path.decode(self.encoding))

    def symlink(self, source, target):
        'creates a symlink `target -> source` (e.g. ln -s source target)'

        return self.operations('symlink', target.decode(self.encoding),
                               source.decode(self.encoding))

    def rename(self, old, new):
        return self.operations('rename', old.decode(self.encoding),
                               new.decode(self.encoding))

    def link(self, source, target):
        'creates a hard link `target -> source` (e.g. ln source target)'

        return self.operations('link', target.decode(self.encoding),
                               source.decode(self.encoding))

    def chmod(self, path, mode):
        return self.operations('chmod', path.decode(self.encoding), mode)

    def chown(self, path, uid, gid):
        # 检查是否有溢出的 -1
        if bs.c_uid_t(uid + 1).value == 0:
            uid = -1
        if bs.c_gid_t(gid + 1).value == 0:
            gid = -1

        return self.operations('chown', path.decode(self.encoding), uid, gid)

    def truncate(self, path, length):
        return self.operations('truncate', path.decode(self.encoding), length)

    def open(self, path, fip):
        fi = fip.contents
        if self.raw_fi:
            return self.operations('open', path.decode(self.encoding), fi)
        else:
            fi.fh = self.operations(
                'open', path.decode(self.encoding), fi.flags)

            return 0

    def read(self, path, buf, size, offset, fip):
        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        ret = self.operations('read', self._decode_optional_path(path), size,
                              offset, fh)

        if not ret:
            return 0

        retsize = len(ret)
        assert retsize <= size, \
            'actual amount read %d greater than expected %d' % (retsize, size)

        ctypes.memmove(buf, ret, retsize)
        return retsize

    def write(self, path, buf, size, offset, fip):
        data = ctypes.string_at(buf, size)

        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('write', self._decode_optional_path(path), data,
                               offset, fh)

    def statfs(self, path, buf):
        stv = buf.contents
        attrs = self.operations('statfs', path.decode(self.encoding))
        for key, val in attrs.items():
            if hasattr(stv, key):
                setattr(stv, key, val)

        return 0

    def flush(self, path, fip):
        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('flush', self._decode_optional_path(path), fh)

    def release(self, path, fip):
        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('release', self._decode_optional_path(path), fh)

    def fsync(self, path, datasync, fip):
        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('fsync', self._decode_optional_path(path), datasync,
                               fh)

    def setxattr(self, path, name, value, size, options, *args):
        return self.operations('setxattr', pathz.decode(self.encoding),
                               name.decode(self.encoding),
                               ctypes.string_at(value, size), options, *args)

    def getxattr(self, path, name, value, size, *args):
        ret = self.operations('getxattr', path.decode(self.encoding),
                              name.decode(self.encoding), *args)

        retsize = len(ret)
        if not value:
            return retsize

        if retsize > size:
            return -errno.ERANGE

        buf = ctypes.create_string_buffer(ret, retsize)
        ctypes.memmove(value, buf, retsize)

        return retsize

    def listxattr(self, path, namebuf, size):
        attrs = self.operations('listxattr', path.decode(self.encoding)) or ''
        ret = '\x00'.join(attrs).encode(self.encoding)
        if len(ret) > 0:
            ret += '\x00'.encode(self.encoding)

        retsize = len(ret)
        if not namebuf:
            return retsize

        if retsize > size:
            return -errno.ERANGE

        buf = ctypes.create_string_buffer(ret, retsize)
        ctypes.memmove(namebuf, buf, retsize)

        return retsize

    def removexattr(self, path, name):
        return self.operations('removexattr', path.decode(self.encoding),
                               name.decode(self.encoding))

    def opendir(self, path, fip):
        # Ignore raw_fi
        fip.contents.fh = self.operations('opendir',
                                          path.decode(self.encoding))

        return 0

    def readdir(self, path, buf, filler, offset, fip):
        # Ignore raw_fi
        for item in self.operations('readdir', self._decode_optional_path(path),
                                    fip.contents.fh):

            if isinstance(item, bs.basestring):
                name, st, offset = item, None, 0
            else:
                name, attrs, offset = item
                if attrs:
                    st = bs.c_stat()
                    set_st_attrs(st, attrs, use_ns=self.use_ns)
                else:
                    st = None

            if filler(buf, name.encode(self.encoding), st, offset) != 0:
                break

        return 0

    def releasedir(self, path, fip):
        # Ignore raw_fi
        return self.operations('releasedir', self._decode_optional_path(path),
                               fip.contents.fh)

    def fsyncdir(self, path, datasync, fip):
        # Ignore raw_fi
        return self.operations('fsyncdir', self._decode_optional_path(path),
                               datasync, fip.contents.fh)

    def init(self, conn):
        return self.operations('init', '/')

    def destroy(self, private_data):
        return self.operations('destroy', '/')

    def access(self, path, amode):
        return self.operations('access', path.decode(self.encoding), amode)

    def create(self, path, mode, fip):
        fi = fip.contents
        path = path.decode(self.encoding)

        if self.raw_fi:
            return self.operations('create', path, mode, fi)
        else:
            fi.fh = self.operations('create', path, mode)
            return 0

    def ftruncate(self, path, length, fip):
        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('truncate', self._decode_optional_path(path),
                               length, fh)

    def fgetattr(self, path, buf, fip):
        ctypes.memset(buf, 0, ctypes.sizeof(bs.c_stat))

        st = buf.contents
        if not fip:
            fh = fip
        elif self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        attrs = self.operations(
            'getattr', self._decode_optional_path(path), fh)
        set_st_attrs(st, attrs, use_ns=self.use_ns)
        return 0

    def lock(self, path, fip, cmd, lock):
        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('lock', self._decode_optional_path(path), fh, cmd,
                               lock)

    def utimens(self, path, buf):
        if buf:
            atime = time_of_timespec(buf.contents.actime, use_ns=self.use_ns)
            mtime = time_of_timespec(buf.contents.modtime, use_ns=self.use_ns)
            times = (atime, mtime)
        else:
            times = None

        return self.operations('utimens', path.decode(self.encoding), times)

    def bmap(self, path, blocksize, idx):
        return self.operations('bmap', path.decode(self.encoding), blocksize,
                               idx)

    def ioctl(self, path, cmd, arg, fip, flags, data):
        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('ioctl', path.decode(self.encoding),
                               cmd, arg, fh, flags, data)
