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

# Docker API location
sockUrl = "unix:///var/run/docker.sock"
# Jinja2 template file location
templateFile = "nginx.conf.tpl"
# Written template save location
targetFile = "/etc/nginx/conf.d/default.conf"
# Default base url
defaultBaseUrl = "example.org"

class MonitorThread(Thread):
    def __init__(self, app, sock):
        super(MonitorThread, self).__init__()

        self.app = app
        self.sock = sock
        self.cli = Client(base_url=self.sock)

    def run(self):
        # Listen for Docker events
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
        # Reset all proxies
        self.proxy = []
        for container in self.cli.containers(all=True):
            # Get first public facing port
            ports = container.get("Ports")
            publicPort = None
            privatePort = None
            for port in ports:
                if "PublicPort" in port:
                    publicPort = port.get("PublicPort")
                    privatePort = port.get("PrivatePort")
                    break
            if publicPort is None:
                continue
            
            # Get container name
            name = container.get("Names")[0]
            name = name.replace('/', '')

            # Get containers private ip
            ip = self.cli.inspect_container(container=container.get("Id")).get("NetworkSettings").get("IPAddress")

            # Add container to proxy list
            self.proxy.append({"name": name, "publicPort": publicPort, "privatePort": privatePort, "hostname": name + "." + self.baseUrl, "privateIp": ip})
        
        # Rewrite template file
        if len(self.proxy) > 0:
            self.writeTemplate()

    def writeTemplate(self):
        # Render and write template
        with open(self.target, "w+") as f:
            f.write(self.template.render(containers=self.proxy))
            print("nginx config file updated")
        # Perform nginx reload
        os.system("nginx -s reload")
        print("nginx reloaded")

if __name__ == "__main__":
    # Get base url from environment
    baseUrl = os.getenv("PROXY_BASE_URL", defaultBaseUrl)
    app = App(sockUrl, baseUrl, templateFile, targetFile)
    # write initial template file
    app.updateProxy()
