# Modsecurity with Molopa

## Modsecurity for Kubernetes, with a new way of logging.

### About
Modsecurity + NGINX reverse proxy inside a Docker image, ready for a Kubernetes deploy. Modsecurity, aswell as upstream servers, are configured through environment variables. Rules can be either retrieved from a repository or configured locally by attacking a folder on the docker container. Personally I didn't liked mlogc as a logging method, that's why I developed molopa (Modsecurity Log Parser), but it's use is optional.
### To-Do
  - [ ] Test latency and jitter.
  - [ ] Add TLS proxy.
  - [ ] Add ClamAV or external Antivirus.
### Download docker image

[Dockerhub](https://hub.docker.com/r/videlanicolas/modsecurity/)

```shell
docker pull videlanicolas/modsecurity
```
### Environment variables
#### Required
   * NGINX_UPSTREAM_SERVERS: Comma/space separated hostname or IP of the NGINX upstream servers.
#### Optional
   * NGINX_USER: NGINX user, default: www-data.
   * NGINX_WORKER_PROCESSES: The amount of worker processes for NGINX, default: 1.
   * NGINX_WORKER_CONNECTIONS: The amount of simultaneous connections handled by NGINX, default 1024.
   * NGINX_LISTEN_PORT: Proxy listen port, default: 80.
   * NGINX_SERVER_NAME: Servername, default: modsecurity.
   * WITH_MOLOPA: Use Molopa for external logging (On/Off), default: Off.
   * WITH_BLOCK_PAGE: Use the HTML on this URL as the blockpage, default: 404.html
   * REMOTE_CONFIG: Download Modsecurity configuration from this URL, default: Local configuration.
   * MODSECURITY_ENGINE: Should Modsecurity intercept HTTP messages (On/Off)? default: On.
   * MODSECURITY_PARSE_REQUEST_BODY: Should Modsecurity parse the Request body (On/Off)? defualt: On.
   * MODSECURITY_PARSE_RESPONSE_BODY: Should Modsecurity parse the Response body (On/Off)? default: On.
   * MODSECURITY_DEBUG: Turn on debug logging (On/Off), default: Off.
### Run
```shell
docker run -d -p 80:80 \
-e NGINX_UPSTREAM_SERVERS='upstreamserver1,upstreamserver2' \
-v /tmp/rules/:/usr/src/modsecurity/rules/ \
videlanicolas/modsecurity
```