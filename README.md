# Supported tags and respective `Dockerfile` links

-	[`regular`, `latest` (*Dockerfile*)](https://github.com/herzog31/docker-proxy/blob/master/regular/Dockerfile)
-	[`ios` (*Dockerfile*)](https://github.com/herzog31/docker-proxy/blob/master/ios/Dockerfile)

# docker-proxy
Nginx proxy that maps containers to subdomains.

Use the `regular` tagged version to map docker containers to subdomains by their name.
**Example:** Container `solid` is mapped to solid.example.org.

Use the `ios` tagged version for the setup used in the iOS Praktikum at TUM to map container compositions to the composition prefix.
**Example:** Containers from a docker composition `liquid_node_1` and `liquid_db_1` are mapped to liquid.example.org.

**Important:** Make sure that your DNS is configured in a way that all subdomains of the given hostname point to your docker host.

## Usage
Run the docker-proxy container using the following command:

```
docker run -it --rm --name docker-proxy -p 80:80 -v /var/run/docker.sock:/var/run/docker.sock -e PROXY_PORT=80 -e PROXY_BASE_URL=example.org herzog31/docker-proxy:regular
```

Replace example.org with the desired hostname and configure your DNS accordingly. All containers that have an exposed port will be reachable via the subdomain.

To let the container run as a daemon, use the following command:

```
docker run -d --name docker-proxy -p 80:80 -v /var/run/docker.sock:/var/run/docker.sock -e PROXY_PORT=80 -e PROXY_BASE_URL=example.org herzog31/docker-proxy:regular
```

## Variables

Variable | Function
--- | --- | ---
PROXY_BASE_URL | Hostname that will be used, e.g. example.org
PROXY_PORT | Public port that will be mapped to the  ports from the containers. Only applicable for the `regular` version.
