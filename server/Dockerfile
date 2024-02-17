FROM alpine

RUN apk add --update --no-cache python3 py3-pip py3-ldap

WORKDIR /app

RUN python3 -m pip install --no-cache-dir --break-system-packages waitress

COPY req.txt .

# remove python-ldap (installed via apk) #
RUN sed -i '/^python-ldap.*$/d' req.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages -r req.txt

# precreate database directory for mount (will otherwise be created at before_first_request)
COPY ./ .
RUN mkdir /app/instance/

EXPOSE 5000/tcp

ENTRYPOINT ["waitress-serve"]
CMD ["--host", "0.0.0.0", "--port", "5000", "--call", "app:createApp" ]
