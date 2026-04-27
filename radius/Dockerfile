FROM freeradius/freeradius-server:3.2.2

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*

COPY raddb/clients.conf.template /opt/ananse-radius/clients.conf.template
COPY raddb/mods-enabled/sql.template /opt/ananse-radius/sql.template
COPY raddb/sites-enabled/default /opt/ananse-radius/default.site
COPY entrypoint.sh /usr/local/bin/ananse-radius-entrypoint.sh

RUN chmod 0644 /opt/ananse-radius/clients.conf.template \
    /opt/ananse-radius/sql.template \
    /opt/ananse-radius/default.site \
 && chmod +x /usr/local/bin/ananse-radius-entrypoint.sh
