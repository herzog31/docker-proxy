# Docker Proxy - NGINX Config Template
# by Mark J. Becker

proxy_set_header 		X-Real-IP  			$remote_addr;
proxy_set_header 		X-Forwarded-For 		$remote_addr;
proxy_set_header 		Host 				$host;

server {
	listen 80 default_server;
	server_name {{ baseUrl }};

	root /usr/share/nginx/html;
    index index.html;
}

{% for container in containers %}
upstream {{ container.fullname }}_{{ container.iPort }} {
	server {{container.ip}}:{{ container.iPort }};
}

server {
	listen {{ container.mPort }};
	access_log /usr/src/app/{{ container.fullname }}_access.log;
	server_name {{ container.hostname }};
	client_max_body_size 100M;

	location / {
		proxy_pass http://{{ container.fullname }}_{{ container.iPort }};
	}
}

{% endfor %}
