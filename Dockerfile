FROM ubuntu:18.04
RUN apt-get update && apt-get install -y supervisor python3.8 python3-pip python3.8-dev
RUN mkdir -p /var/log/supervisor

RUN python3.8 -m pip install hpfeeds twisted msgpack pyzmq

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY honeypot/honeypot_app.py /usr/local/bin/honeypot_app
COPY honeypot/proxy_logger.py /usr/local/bin/proxy_logger

RUN chmod +x /usr/local/bin/honeypot_app /usr/local/bin/proxy_logger

CMD ["/usr/bin/supervisord"]

