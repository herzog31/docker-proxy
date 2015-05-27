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
# Jinja2 template file location and destination
templateFiles = [("nginx.conf.tpl", "/etc/nginx/conf.d/default.conf"), ("index.tpl", "/usr/share/nginx/html/index.html")]
# Written template save location
# targetFile = "/etc/nginx/conf.d/default.conf"
# Default base url
defaultBaseUrl = "example.org"
# Events that trigger template creation
dockerEvents = ['start', 'destroy']
# Default port range
defaultPortRange = "80-100"

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

    def __init__(self, sock, baseUrl, templateFiles, dockerEvents, portRange):
        self.sock = sock
        self.proxy = []
        # self.target = targetFile
        self.baseUrl = baseUrl
        self.cli = Client(base_url=self.sock)
        self.monitor = MonitorThread(self, sockUrl, dockerEvents).start()
        self.jinjaenv = Environment(loader=FileSystemLoader('.'), trim_blocks=True)
        self.templateFiles = templateFiles
        self.ownHostname = os.getenv("HOSTNAME", "false")
        self.portRangeFrom = int(portRange.split("-")[0])
        self.portRangeTo = int(portRange.split("-")[1])

    def updateProxy(self):
        # Reset all proxies
        self.proxy = []
        self.portMappings = {}

        for container in self.cli.containers(all=True):

            # Get container ID
            containerId = container.get("Id")

            # Skip itself
            if containerId.startswith(self.ownHostname): continue

            # Get container name
            fullname = container.get("Names")[0]
            fullname = fullname.replace('/', '')
            # Get project name part of container name
            name = fullname.split('_')[0]

            # Get containers private ip
            try:
                inspect = self.cli.inspect_container(container=containerId)
                ip = inspect.get("NetworkSettings").get("IPAddress")
            except:
                continue

            # Get all public facing ports
            ports = container.get("Ports")
            publicPorts = []
            for port in ports:
                if "PublicPort" in port:
                    publicPorts.append((int(port.get("PublicPort")), int(port.get("PrivatePort"))))

            # Sort
            publicPorts = sorted(publicPorts, key=lambda ports: ports[1])

            for port in publicPorts:
                # Find mapping port
                if name in self.portMappings:
                    self.portMappings[name] = self.portMappings[name] + 1
                else:
                    self.portMappings[name] = self.portRangeFrom

                mapPort = self.portMappings[name]

                # Skip container if mapping port range is exceeded
                if mapPort > self.portRangeTo: break

                # Add container to proxy list
                self.proxy.append({"name": name, "fullname": fullname, "publicPort": port[0], "privatePort": port[1], "mapPort": mapPort, "hostname": name + "." + self.baseUrl, "privateIp": ip})
        
        # Rewrite template file
        self.writeTemplate()

    def writeTemplate(self):
        # Render and write templates
        for template in self.templateFiles:
            with open(template[1], "w+") as f:
                tplFile = self.jinjaenv.get_template(template[0])
                f.write(tplFile.render(containers=self.proxy, baseUrl=self.baseUrl))

        # Perform nginx reload
        os.system("nginx -s reload")
        print("Templates updated and nginx reloaded!")

if __name__ == "__main__":
    # Get base url from environment
    baseUrl = os.getenv("PROXY_BASE_URL", defaultBaseUrl)
    portRange = os.getenv("PROXY_PORT_RANGE", defaultPortRange)
    app = App(sockUrl, baseUrl, templateFiles, dockerEvents, portRange)

    # write initial template file
    app.updateProxy()