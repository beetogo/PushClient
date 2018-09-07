import logging
import os
import platform
import threading
import time

import psutil
from socketIO_client import SocketIO, BaseNamespace

import config

NETWORK_IN = 0
NETWORK_OUT = 0


def push_client(namespace):
    while True:
        # 获取信息
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        netio = psutil.net_io_counters()
        sysstr = platform.system()
        load = 'None'

        # 判断是否为Linux系统 是则设置负载
        if sysstr == "Linux":
            load = str(os.getloadavg())

        # 构造发送数据
        data = {
            'uuid': config.PUSH_SERVER_UUID,
            'token': config.PUSH_SERVER_TOKEN,
            'cpu_precent': psutil.cpu_percent(interval=1),
            'memory': mem.total - mem.available,
            'memory_all': mem.total,
            'update_time': round(time.time() * 1000),
            'uptime': (int(time.time()) - psutil.boot_time()) * 1000,
            'load': load,
            'network_in': NETWORK_IN,
            'network_out': NETWORK_OUT,
            'traffic_in': netio.bytes_recv,
            'traffic_out': netio.bytes_sent,
            'hdd': disk.used,
            'hdd_all': disk.total
        }

        # 发送
        namespace.emit('server_push', data)
        # 延迟
        # time.sleep(0.5)


def network_io():
    while True:
        netio = psutil.net_io_counters()
        time.sleep(1)
        netio_new = psutil.net_io_counters()

        global NETWORK_IN, NETWORK_OUT
        NETWORK_IN = netio_new.bytes_recv - netio.bytes_recv
        NETWORK_OUT = netio_new.bytes_sent - netio.bytes_sent


class Namespace(BaseNamespace):
    __info_count = 0

    def on_connect(self):
        logging.info('Server connected')

    def on_reconnect(self):
        logging.info('Server reconnected')

    def on_disconnect(self):
        logging.info('Server Disconnected')

    def on_server_push(self, args):
        # 判断收到的数据是否正确
        if not args['status']:
            logging.error('Return error data : %s' % args)
            return

        # 定期输出连接状态
        self.__info_count += 1
        self.__info_count += 1
        if self.__info_count % 1800 == 0:
            logging.info('Connection status: connected')


def main():
    # 设置日志格式
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    logging.info('PushClient - Powered by @FanHuaCloud')
    logging.info('Versions : %s | ServerIP : %s | ServerPort : %s' % (
        config.VERSION, config.PUSH_SERVER_IP, config.PUSH_SERVER_PORT))
    # 开启SocketIO
    socketio = SocketIO(config.PUSH_SERVER_IP, config.PUSH_SERVER_PORT)
    chat_namespace = socketio.define(Namespace, '/info')

    # 创建线程并开启
    t_push_client = threading.Thread(target=push_client, args=(chat_namespace,), daemon=True)
    t_network_io = threading.Thread(target=network_io, daemon=True)
    t_push_client.start()
    t_network_io.start()

    logging.info('Server push thread success')

    # 阻塞
    socketio.wait()


if __name__ == '__main__':
    main()
