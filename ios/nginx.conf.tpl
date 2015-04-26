# Docker Proxy - NGINX Config Template
# by Mark J. Becker

proxy_set_header 		X-Real-IP  			$remote_addr;
proxy_set_header 		X-Forwarded-For 	$remote_addr;
proxy_set_header 		Host 				$host;

server {
	listen 80 default_server;
	server_name {{ baseUrl }};

	root /usr/share/nginx/html;
    index index.html;
}

{% for container in containers %}
upstream {{ container.name }}_{{ container.privatePort }} {
	server {{container.privateIp}}:{{ container.privatePort }};
}

server {
	listen {{ container.mapPort }};
	access_log /usr/src/app/{{ container.name }}_access.log;
	server_name {{ container.hostname }};

	location / {
		proxy_pass http://{{ container.name }}_{{ container.privatePort }};
	}
}

{% endfor %}
