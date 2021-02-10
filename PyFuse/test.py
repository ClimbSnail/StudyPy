#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import logging
import memory
import time
import os


class MemoryTest(unittest.TestCase):
    def setUp(self):
        print("call setUp: ")
        ret = os.popen("python3 memory.py mount_test").read()

    def tearDown(self):
        ret = os.popen("umount mount_test").read()
        ret = os.popen("rm -rf mount_test").read()
        ret = os.popen("rm -rf memory.pyc base_struct.pyc fuse.pyc").read()
        print("call tearDown.\n")

    def test_write(self):
        expect = os.popen("ls ./mount_test").read()
        os.popen("cp ./test.py ./mount_test/")
        time.sleep(0.2)
        ret = os.popen("ls ./mount_test").read()
        os.popen("rm -rf ./mount_test/test.py")
        self.assertNotEqual(ret, expect)

    def test_open(self):
        expect = os.popen("cat ./test.py").read()
        os.popen("cp ./test.py ./mount_test/")
        time.sleep(0.2)
        ret = os.popen("cat mount_test/test.py").read()
        os.popen("rm -rf ./mount_test/test.py")
        self.assertEqual(ret, expect)

    def test_create(self):
        expect = "hello world"
        os.popen("echo %s >> ./mount_test/new_file" % expect).read()
        ret = os.popen("cat ./mount_test/new_file").read()
        os.popen("rm -rf ./mount_test/new_file")
        self.assertEqual(ret, expect+"\n")

    def test_chmod(self):
        os.popen("cp ./test.py ./mount_test/")
        time.sleep(0.2)
        os.popen("chmod 755 ./mount_test/test.py")
        time.sleep(0.2)
        ret = os.popen("ls -l ./mount_test/").readlines()[1].split()[0]
        os.popen("chmod 777 ./mount_test/test.py")
        time.sleep(0.2)
        expect = os.popen("ls -l ./mount_test/").readlines()[1].split()[0]
        succ_flag = True if ret != expect and expect == "-rwxrwxrwx" else False
        self.assertTrue(succ_flag)


if __name__ == "__main__":
    unittest.main()
