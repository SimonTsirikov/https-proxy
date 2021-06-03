#!/usr/bin/env python3
# coding=utf-8


import socket
from threading import Thread


class Proxy:
    def __init__(self, host="0.0.0.0", port=3000):
        self.host = host
        self.port = port
        self.proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buffer_size = 4096


    def run(self):
        self.proxy.bind((self.host, self.port))
        self.proxy.listen(100)
        while True:
            client, addr = self.proxy.accept()
            print(f"Accept {addr[0]}:{addr[1]}")
            Thread(target=self.handle_request, args=(client, )).start()


    def handle_request(self, client):
        data = self.parse(client.recv(self.buffer_size))
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((data["host"], data["port"]))

        if data["meta"].startswith("CONNECT"):
            client.sendall("HTTP/1.1 200 OK\r\n\r\n".encode())
            
            client.setblocking(False)
            server.setblocking(False)

            while True:
                try:
                    data = client.recv(self.buffer_size)
                    if (not data):
                        client.close()
                        break
                    server.sendall(data)
                except socket.error as e:
                    pass
                try:
                    reply = server.recv(self.buffer_size)
                    if (not reply):
                        server.close()
                        break
                    client.sendall(reply)
                except socket.error as e:
                    pass
            server.close()
            client.close()
        else:
            server.sendall(data["source"])

            response = server.recv(self.buffer_size)
            while (not response.endswith(b"\r\n\r\n")):
                response += server.recv(self.buffer_size)
            
            client.sendall(response)
            server.close()
            client.close()


    def parse(self, request):
        nodes = request.split(b"\r\n\r\n")
        heads = nodes[0].split(b"\r\n")

        data = {
            "meta": heads.pop(0).decode("utf-8"),
            "headers": {},
            "chunk": b"",
            "host": "",
            "port": 80,
            "source": request
        }

        if len(nodes) >= 2:
            data["chunk"] = nodes[1]

        for head in heads:
            k, v = head.split(b": ")
            data["headers"][k.decode("utf-8")] = v.decode("utf-8")

        tmp = data["headers"]["Host"].split(":")
        data["host"] = tmp[0]
        if (len(tmp) == 2):
            data["port"] = int(tmp[1])

        return data


if __name__ == "__main__":
    Proxy(host='0.0.0.0', port=3000).run()
