#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=True, engineio_logger=True)





@app.route('/')
def index():
    return render_template('websocket_test.html')

# 触发事件my event：回复只发送此连接

# 下面指定的namespace，若客户端要连接到此namespace时 需要指定 io.connect(url/chat)。
@socketio.on('my_event', namespace='/chat')
def test_message(message):
    print("my_event -> " + str(message) )
    emit('my_response', {'data': message['data']})
    while True:
        time.sleep(2)
        emit('my_response', {'data': message['data']})


# 触发事件my broadcast event：：回复所有链接（广播）
@socketio.on('my_broadcast event')
def test_message(message):
    print("my_broadcast event -> " + str(message))
    emit('my_response', {'data': message['data']}, broadcast=True)

##################################################################
# 自动连接和自动断开触发


@socketio.on('connect', namespace='/chat')
def test_connect():
    print("连接到来")
    emit('my_response', {'data': 'Connected'})


@socketio.on('disconnect', namespace='/chat')
def test_disconnect():
    print("连接断开")
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=8200, debug=True)

