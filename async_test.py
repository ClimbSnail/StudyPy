
def test_1():
    async def func1():
        print("func1 start")
        print("func1 end")

    async def func2():
        print("func2 start")
        print("func2 a")
        print("func2 b")
        print("func2 c")
        print("func2 end")

    f1 = func1()
    f2 = func2()
    print(f1, f2)

    try:
        print('f2.send')
        f2.send(None)
    except StopIteration as e:
        pass

    try:
        print('f1.send')
        f1.send(None)
    except StopIteration as e:  # 这里也是需要去捕获StopIteration方法
        pass

def test_2():
    import asyncio

    async def hello():
        print('Hello ...')
        await asyncio.sleep(5)
        print('... World!')

    async def main():
        await asyncio.gather(hello(), hello(), hello(), hello(), hello())

    asyncio.run(main())


def test_3():
    import time

    def hello():
        print('Hello ...')
        time.sleep(5)
        print('... World!')

    def main():
        hello(), hello()

    main()


import time
time_start = time.time()
test_2()
print(time.time()-time_start)