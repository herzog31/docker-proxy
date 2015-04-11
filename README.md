# docker-proxy
Nginx proxy that maps containers to subdomains by their names

# Usage
docker run -it --rm --name docker-proxy -v /var/run/docker.sock:/var/run/docker.sock -e PROXY_BASE_URL="marb.ec" docker-proxy
