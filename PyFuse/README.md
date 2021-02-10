快速开始
---
#### 运行
1. `python3 memory.py mount`即可运行本程序。此内存文件系统将会被挂载到当前目录的mount目录中。
2. 之后就可以在其他终端中使用linux命令查看挂载的内存memoryfs（mount目录）。例如`ll`、`cd`、`cp`。命令中，对文件的操作自动写入RAM中。
文件介绍（代码文件一共有三个）
---
1. base_struct.py 存放python与C对应的数据结构。
2. fuse.py 封装的一个通用fuse的框架（接口类）。
3. memory.py 为本次具体实现的内存文件系统的代码。
设计思路
---
1. 提供`Operations`接口类，提供所有fuse的方法集合。所有具体实现的类都要继承本接口，重写需要的接口。
2. `FuseOperations`类定义了与内核fuse回调关系的函数集合，用于将用户实现的方法捆绑到内核的回调里。
3. `Fuse`类为主控类，用于屏蔽公共文件系统必须且复杂的一些操作，简化具体用户实现类的编写工作。
4. `Memory`类为本次具体实现的内存文件系统类，继承于`Operations`接口类。
# PyFuse
使用python实现fuse接口
