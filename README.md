# Supported tags and respective `Dockerfile` links

-	[`regular`, `latest` (*Dockerfile*)](https://github.com/herzog31/docker-proxy/blob/master/regular/Dockerfile)
-	[`ios` (*Dockerfile*)](https://github.com/herzog31/docker-proxy/blob/master/ios/Dockerfile)

# docker-proxy
Nginx proxy that maps containers to subdomains.

Use the `regular` tagged version to map docker containers to subdomains by their name.

**Example:** Container `solid` is mapped to solid.example.org. The containers public port is mapped to the port specified via `PROXY_PORT`.

---

Use the `ios` tagged version for the setup used in the iOS Praktikum at TUM to map container compositions to the composition prefix.

**Example:** Containers from a docker composition `liquid_node_1` and `liquid_db_1` are mapped to `liquid.example.org`. The container's private ports are mapped to the new subdomain if a public mapping exists, respecting docker-proxy's published port range. So the first public port of `liquid_node_1` is available at `liquid.example.org:80`, the second at `liquid.example.org:81` etc.

---

**Important:** Make sure that your DNS is configured in a way that all subdomains of the given hostname point to your docker host.

## Usage
Run the docker-proxy container using the following command:

### Regular Version

```
docker run -it --rm --name docker-proxy -p 80:80 -v /var/run/docker.sock:/var/run/docker.sock -e PROXY_PORT=80 -e PROXY_BASE_URL=example.org herzog31/docker-proxy:regular
```

### iOS Version

```
docker run -it --rm --name docker-proxy -p 80-200:80-200 -v /var/run/docker.sock:/var/run/docker.sock -e PROXY_PORT_RANGE=80-200 -e PROXY_BASE_URL=example.org herzog31/docker-proxy:ios
```

Replace `example.org` with the desired hostname and configure your DNS accordingly.

---

To let the container run as a daemon, use the following command:

### Regular Version

```
docker run -d --name docker-proxy --restart=always -p 80:80 -v /var/run/docker.sock:/var/run/docker.sock -e PROXY_PORT=80 -e PROXY_BASE_URL=example.org herzog31/docker-proxy:regular
```

### iOS Version

```
docker run -d --name docker-proxy --restart=always -p 80-200:80-200 -v /var/run/docker.sock:/var/run/docker.sock -e PROXY_PORT_RANGE=80-200 -e PROXY_BASE_URL=example.org herzog31/docker-proxy:ios
```

## Port Mappings Overview

The proxy provides an overview table at `example.org:80` that shows all port mappings.

## Variables

Variable | Function
--- | --- | ---
PROXY_BASE_URL | Hostname that will be used, e.g. example.org
PROXY_PORT | Public port that will be mapped to the ports from the containers. Only applicable for the `regular` version.
PROXY_PORT_RANGE | Public ports that will be mapped to the ports form the containers. Only applicable for the `ios` version.
