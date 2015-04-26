# Docker Proxy - NGINX Config Template
# by Mark J. Becker

proxy_set_header 		X-Real-IP  			$remote_addr;
proxy_set_header 		X-Forwarded-For 	$remote_addr;
proxy_set_header 		Host 				$host;

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
	listen {{ container.privatePort }};
	access_log /usr/src/app/{{ container.name }}_access.log;
	server_name {{ container.hostname }};

	location / {
		proxy_pass http://{{ container.name }};
	}
}

{% endfor %}
