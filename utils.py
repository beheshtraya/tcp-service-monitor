import asyncore
import socket


class MockService(asyncore.dispatcher):
    def __init__(self, host, port):
        super(MockService, self).__init__()
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind((host, port))
        self.address = self.socket.getsockname()
        self.listen(1)

    def handle_close(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.close()


m = MockService('127.0.0.1', 9008)
try:
    asyncore.loop()
except Exception as e:
    print(str(e))
    m.close()
