'''
Docker Proxy
Container Monitor

@author Mark J. Becker <mjb@marb.ec>
'''

import os
from threading import Thread
from docker import Client
from jinja2 import Template, Environment, FileSystemLoader
import json

sockUrl = "unix:///var/run/docker.sock"
templateFile = "nginx.conf.tpl"
targetFile = "/etc/nginx/conf.d/default.conf"

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

    def __init__(self, sock, baseUrl, templateFile, targetFile):
        self.sock = sock
        self.proxy = []
        self.target = targetFile
        self.baseUrl = baseUrl
        self.cli = Client(base_url=self.sock)
        self.monitor = MonitorThread(self, sockUrl).start()
        self.jinjaenv = Environment(loader=FileSystemLoader('.'), trim_blocks=True)
        self.template = self.jinjaenv.get_template(templateFile)

    def updateProxy(self):
        self.proxy = []
        for container in self.cli.containers(all=True):
            ports = container.get("Ports")
            print(ports)
            publicPort = None
            privatePort = None
            for port in ports:
                if "PublicPort" in port:
                    publicPort = port.get("PublicPort")
                    privatePort = port.get("PrivatePort")
            if publicPort is not None:
                name = container.get("Names")[0]
                name = name.replace('/', '')
                ip = self.cli.inspect_container(container=container.get("Id")).get("NetworkSettings").get("IPAddress")
                self.proxy.append({"name": name, "publicPort": publicPort, "privatePort": privatePort, "hostname": name + "." + self.baseUrl, "privateIp": ip})
        if len(self.proxy) > 0:
            self.writeTemplate()

    def writeTemplate(self):
        with open(self.target, "w+") as f:
            f.write(self.template.render(containers=self.proxy))
            print("nginx config file updated")
        with open(self.target, "r") as f:
            print(f.read())
        os.system("nginx -s reload")
        print("nginx releaded")

if __name__ == "__main__":
    baseUrl = os.getenv("PROXY_BASE_URL", "marb.ec")
    app = App(sockUrl, baseUrl, templateFile, targetFile)
    app.updateProxy()
