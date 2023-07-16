FROM python:3.9-slim-buster

RUN apt update
RUN apt install python3-pip -y
RUN python3 -m pip install --upgrade pip
RUN apt install curl -y
RUN apt autoremove -y
RUN apt clean

WORKDIR /app

RUN python3 -m pip install waitress

COPY req.txt .
RUN python3 -m pip install --no-cache-dir -r req.txt

# precreate database directory for mount (will otherwise be created at before_first_request)
COPY ./ .
RUN mkdir /app/instance/

EXPOSE 5000/tcp

ENTRYPOINT ["waitress-serve"]
CMD ["--host", "0.0.0.0", "--port", "5000", "--call", "app:createApp" ]
