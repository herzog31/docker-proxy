# docker-proxy
Nginx proxy that maps containers to subdomains by their names

## Usage
Run the container using the following command:

```
docker run -it \-\-rm \-\-name docker-proxy -p 80:80 -v /var/run/docker.sock:/var/run/docker.sock -e PROXY_BASE_URL=example.org herzog31/docker-proxy
```

Replace example.org with the desired hostname and configure your DNS accordingly. All containers that have an exposed port will be available at `http://containername.example.org:80`.

To let the container run as a daemon, use the following command:

```
docker run -d \-\-name docker-proxy -p 80:80 -v /var/run/docker.sock:/var/run/docker.sock -e PROXY_BASE_URL=example.org herzog31/docker-proxy
```
