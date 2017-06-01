#! /usr/bin/python
import os, re

def create_config(nginx_location='/usr/local/nginx/conf/nginx.conf'):
	proxylist = ''
	for ip in re.split(',|;|\*| ',os.environ['NGINX_UPSTREAM_SERVERS']):
		proxylist+='server {0};'.format(ip)
	data = """
user  {0};
worker_processes  {1};
daemon off;

events {{
    worker_connections  {2};
}}

http {{
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    access_log off;
    
    keepalive_timeout  65;

    server {{
        listen       {3};
        server_name  {4};

        location / {{
	    ModSecurityEnabled on;
		ModSecurityConfig /usr/src/modsecurity/modsecurity.conf;
		proxy_pass http://upstream_servers;
		proxy_read_timeout 180s;
        }}
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {{
            root   html;
        }}
    }}
upstream upstream_servers {{
{5}    
}}
}}
""".format(	os.environ['NGINX_USER'] if 'NGINX_USER' in os.environ else 'www-data',\
			os.environ['NGINX_WORKER_PROCESSES'] if 'NGINX_WORKER_PROCESSES' in os.environ else '1',\
			os.environ['NGINX_WORKER_CONNECTIONS'] if 'NGINX_WORKER_CONNECTIONS' in os.environ else '1024',\
			os.environ['NGINX_LISTEN_PORT'] if 'NGINX_LISTEN_PORT' in os.environ else '80',\
			os.environ['NGINX_SERVER_NAME'] if 'NGINX_SERVER_NAME' in os.environ else 'modsecurity',\
			proxylist)
	with open(nginx_location,'w') as f:
		f.write(data)

if __name__ == '__main__':
	try:
		create_config()
	except Exception as e:
		print "Error generating configuration for NGINX: {0}".format(str(e))
		exit(1)
	else:
		exit(0)