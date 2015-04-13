# Docker Proxy - nginx config
# by Mark J. Becker

server {
	listen 80 default_server;
	server_name _;
	return 404;
}

{% for container in containers %}
upstream {{ container.name }} {
	server {{container.privateIp}}:{{ container.privatePort }};
}

server {
	listen 80;
	access_log /usr/src/app/access.log;
	server_name {{ container.hostname }};

	location / {
		proxy_pass http://{{ container.name }};
	}
}

{% endfor %}
