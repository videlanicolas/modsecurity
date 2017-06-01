FROM ubuntu:xenial
#Labels
LABEL version="3.0" author="Nicolas Videla" description="ModSecurity with NGINX"

#Dependencies
RUN apt-get update && \
	apt-get install -y --no-upgrade --no-install-recommends git wget build-essential libpcre3 libpcre3-dev libssl-dev libtool autoconf apache2-dev libxml2-dev libcurl4-openssl-dev python python-pip libmysqlclient-dev python-dev python-setuptools unzip automake cron &&\
	pip install --upgrade pip &&\
	pip install wheel &&\
	pip install argparse mysql-python SQLAlchemy mysql-connector-python-rf setuptools

###Download Source Code###
#Download modsecurity
RUN cd /usr/src &&\
	wget https://github.com/SpiderLabs/ModSecurity/archive/v2.9.1.zip &&\
	unzip v2.9.1.zip &&\
	mv ModSecurity-2.9.1 modsecurity &&\
	rm -f v2.9.1.zip

#Download NGINX
RUN cd /tmp &&\
	wget http://nginx.org/download/nginx-1.9.9.tar.gz &&\
	tar -xzf nginx-1.9.9.tar.gz

#Compile modsecurity
RUN cd /usr/src/modsecurity/ && \
	./autogen.sh && \
	./configure --enable-standalone-module --disable-mlogc && \
	make

#Compile NGINX
RUN cd /tmp/nginx-1.9.9 && \
	 ./configure --user=www-data --group=www-data --add-module=/usr/src/modsecurity/nginx/modsecurity && \
	 make && \
	 make install

##Creating modsecurity folders
#Logs -> /var/log/modsecurity/data
#Logs -> /var/log/modsecurity/
#Logs -> /var/log/modsecurity/
#Captured binaries -> /opt/modsecurity/bin
#Configuration -> /etc/modsecurity
#ln Rules -> /etc/modsecurity/rules.d/
#Rules -> /etc/modsecurity/rules/
#Temp -> /tmp
##Upload files -> /var/upload

RUN mkdir -p 	/var/log/modsecurity/data \
				/var/log/modsecurity/audit \
				/opt/modsecurity/bin \
				/etc/modsecurity/rules.d \
				/etc/modsecurity/rules \
				/var/upload

###OWASP###
###RUN git -C /usr/src/ clone https://github.com/SpiderLabs/owasp-modsecurity-crs.git
#RUN cp -R /usr/src/owasp-modsecurity-crs/rules/* /etc/modsecurity/rules/
###RUN cp /usr/src/owasp-modsecurity-crs/crs-setup.conf.example /etc/modsecurity/rules/crs-setup.conf

COPY conf/modsecurity.conf /usr/src/modsecurity/modsecurity.conf

COPY conf/molopa.py /usr/bin/molopa
COPY conf/fetch_modsecurity_configuration.py /usr/bin/fetch_modsecurity_configuration
RUN chmod +x /usr/bin/molopa &&\
	useradd -M -s /bin/false -G www-data molopa &&\
	chown -R www-data:www-data /var/log/modsecurity

#Create NGINX configuration
COPY conf/nginxconf.py /usr/bin/nginxconf
COPY bad.html /usr/local/nginx/html/bad.html

#Fix to enable unicode mapping
RUN cp /usr/src/modsecurity/unicode.mapping /usr/local/nginx/conf/

#Uninstall unneccessary things
RUN apt-get remove --purge -y unzip git automake build-essential wget python-pip python-setuptools autoconf

#Expose HTTP
EXPOSE 80/tcp

COPY bootstrap.sh /usr/bin/bootstrap

#Run NGINX
ENTRYPOINT bootstrap