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
# Default proxy port
defaultProxyPort = "80"
# Events that trigger template creation
dockerEvents = ['start', 'destroy']

class MonitorThread(Thread):
    def __init__(self, app, sock, dockerEvents):
        super(MonitorThread, self).__init__()

        self.app = app
        self.sock = sock
        self.dockerEvents = dockerEvents
        self.cli = Client(base_url=self.sock)

    def run(self):
        # Listen for Docker events
        for event in self.cli.events():
            event = json.loads(event.decode('utf-8'))
            if event.get("status") in self.dockerEvents:
                self.app.updateProxy()

    def stop(self):
        self.cli.close()

class App():

    def __init__(self, sock, baseUrl, templateFile, targetFile, proxyPort, dockerEvents):
        self.sock = sock
        self.proxy = []
        self.target = targetFile
        self.baseUrl = baseUrl
        self.proxyPort = proxyPort
        self.cli = Client(base_url=self.sock)
        self.monitor = MonitorThread(self, sockUrl, dockerEvents).start()
        self.jinjaenv = Environment(loader=FileSystemLoader('.'), trim_blocks=True)
        self.template = self.jinjaenv.get_template(templateFile)
        self.ownHostname = os.getenv("HOSTNAME", "false")

    def updateProxy(self):
        # Reset all proxies
        self.proxy = []
        for container in self.cli.containers(all=True):

            # Get container ID
            containerId = container.get("Id")

            # Skip itself
            if containerId.startswith(self.ownHostname): continue

            # Get first public facing port
            ports = container.get("Ports")
            publicPort = None
            privatePort = None
            for port in ports:
                if "PublicPort" in port:
                    publicPort = port.get("PublicPort")
                    privatePort = port.get("PrivatePort")
                    break
            if publicPort is None: continue
            
            # Get container name
            name = container.get("Names")[0]
            name = name.replace('/', '')

            # Get containers private ip
            try:
                inspect = self.cli.inspect_container(container=containerId)
                ip = inspect.get("NetworkSettings").get("IPAddress")
            except:
                continue

            # Add container to proxy list
            self.proxy.append({"name": name, "publicPort": publicPort, "privatePort": privatePort, "hostname": name + "." + self.baseUrl, "privateIp": ip})
        
        # Rewrite template file
        self.writeTemplate()

    def writeTemplate(self):
        # Render and write template
        with open(self.target, "w+") as f:
            f.write(self.template.render(containers=self.proxy, proxyPort=self.proxyPort))
            print("nginx config file updated")

        # Perform nginx reload
        os.system("nginx -s reload")
        print("nginx reloaded")

if __name__ == "__main__":
    # Get base url from environment
    baseUrl = os.getenv("PROXY_BASE_URL", defaultBaseUrl)
    proxyPort = os.getenv("PROXY_PORT", defaultProxyPort)
    app = App(sockUrl, baseUrl, templateFile, targetFile, proxyPort, dockerEvents)

    # write initial template file
    app.updateProxy()