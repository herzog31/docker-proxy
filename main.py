import os
from threading import Thread
from docker import Client
import json

sockUrl = "unix:///var/run/docker.sock"

class MonitorThread(Thread):
    def __init__(self, app, sock):
        super(MonitorThread, self).__init__()

        self.app = app
        self.sock = sock
        self.cli = Client(base_url=self.sock)

    def run(self):
        for event in self.cli.events():
            event = json.loads(event.decode('utf-8'))
            print(json.dumps(event, indent=4))

            self.app.updateProxy()

    def stop(self):
        self.cli.close()

class App():

    def __init__(self, sock, baseUrl):
        self.sock = sock
        self.baseUrl = baseUrl
        self.cli = Client(base_url=self.sock)
        self.monitor = MonitorThread(self, sockUrl).start()

    def updateProxy(self):
        for container in self.cli.containers(all=True):
            ports = container.get("Ports")
            publicPort = None
            for port in ports:
                if "PublicPort" in port:
                    publicPort = port.get("PublicPort")
            if publicPort is not None:
                name = container.get("Names")[0]
                name = name.replace('/', '')
                print("Container with name " + name + " is reachable at port " + str(publicPort) + " -> http://" + name + "." + self.baseUrl + "/")

if __name__ == "__main__":
    baseUrl = os.getenv("PROXY_BASE_URL", "marb.ec")
    app = App(sockUrl, baseUrl)
