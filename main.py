from threading import Thread
from docker import Client
import json

class MonitorThread(Thread):
    def __init__(self, sock):
        super(MonitorThread, self).__init__()

        self.sock = sock
        self.cli = Client(base_url=self.sock)

    def run(self):
        for event in self.cli.events():
            event = json.loads(event.decode('utf-8'))
            print(json.dumps(event, indent=4))

    def stop(self):
        self.cli.close()

def main():
    sockUrl = "unix:///var/run/docker.sock"

    MonitorThread(sockUrl).start()

if __name__ == "__main__":
    main()
