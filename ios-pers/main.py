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
import copy

# Docker API location
sockUrl = "unix:///var/run/docker.sock"
# Jinja2 template file location and destination
templateFiles = [("nginx.conf.tpl", "/etc/nginx/conf.d/default.conf"), ("index.tpl", "/usr/share/nginx/html/index.html")]
# Default base url
defaultBaseUrl = "example.org"
# Events that trigger template creation
dockerEvents = ['start', 'destroy']
# Default port range
defaultPortRange = "80-100"
# Mapping file
mappingFile = "mappings.json"

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
        self.baseUrl = baseUrl
        self.cli = Client(base_url=self.sock)
        self.monitor = MonitorThread(self, sockUrl, dockerEvents).start()
        self.jinjaenv = Environment(loader=FileSystemLoader('.'), trim_blocks=True)
        self.templateFiles = templateFiles
        self.ownHostname = os.getenv("HOSTNAME", "false")
        self.portRangeFrom = int(portRange.split("-")[0])
        self.portRangeTo = int(portRange.split("-")[1])
        self.savedMappings = []

    def loadPortMappings(self):
        # Load saved mappings
        self.savedMappings = []
        with open(mappingFile, "r") as f:
            self.savedMappings = json.load(f)
        for mapping in self.savedMappings:
            if mapping["project"] not in self.portMappings:
                self.portMappings[mapping["project"]] = []
            self.portMappings[mapping["project"]].append(mapping["mPort"])

    def savePortMappings(self, mappings):
        # Save all mappings into json file
        with open(mappingFile, "w+") as f:
            json.dump(mappings, f)
        return

    def applyMappingsForContainers(self):
        # Check for each container if a mapping was saved
        for i, container in enumerate(self.containers):
            if container is None:
                continue
            for mapping in self.savedMappings:
                if mapping["fullname"] == container["fullname"] and int(mapping["iPort"]) == container["iPort"]:
                    container["mPort"] = mapping["mPort"]
                    proxyEntry = copy.copy(container)
                    proxyEntry["hostname"] = container["project"] + "." + self.baseUrl
                    self.proxy.append(proxyEntry)
                    print("Use saved port mapping for container "+container["fullname"]+": "+str(container["iPort"])+" -> "+str(mapping["mPort"]))
                    self.containers[i] = None
                    break

    def updateProxy(self):
        # Reset all proxy entries
        self.proxy = []
        # Container buffer
        self.containers = []
        # Port mappings
        self.portMappings = {}

        for container in self.cli.containers(all=True):

            # Get container ID
            containerId = container.get("Id")

            # Skip itself
            if containerId.startswith(self.ownHostname): continue

            # Get full container name
            fullname = container.get("Names")[0]
            for name in container.get("Names"):
                if name.count('/') == 1:
                    fullname = name
            fullname = fullname.replace('/', '')

            # Get project and conainer name part of name
            project = fullname.split('_')[0]
            name = fullname[len(project)+1:]

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

            # Buffer containers
            for port in publicPorts:
                self.containers.append({"id": containerId, "fullname": fullname, "project": project, "name": name, "ip": ip, "iPort": port[1], "oPort": port[0]})

        # Load saved mappings
        self.loadPortMappings()

        # Check for each container if a mapping was saved
        self.applyMappingsForContainers()

        # Choose random mapping for containers without saved mapping
        for i, container in enumerate(self.containers):
            if container is None:
                continue
            if container["project"] not in self.portMappings:
                self.portMappings[container["project"]] = []
            mPort = self.portRangeFrom
            while (mPort in self.portMappings[container["project"]]):
                mPort += 1
                if mPort > self.portRangeTo:
                    break

            self.portMappings[container["project"]].append(mPort)
            container["mPort"] = mPort
            proxyEntry = copy.copy(container)
            proxyEntry["hostname"] = container["project"] + "." + self.baseUrl
            mappingEntry = copy.copy(container)
            del mappingEntry["oPort"]
            del mappingEntry["ip"]
            del mappingEntry["id"]
            self.proxy.append(proxyEntry)
            self.savedMappings.append(mappingEntry)
            print("Use random port mapping for container "+container["fullname"]+": "+str(container["iPort"])+" -> "+str(container["mPort"]))
            self.containers[i] = None
            self.applyMappingsForContainers()

        # Merge with existing
        self.savePortMappings(self.savedMappings)

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
