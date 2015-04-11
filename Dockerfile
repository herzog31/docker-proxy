FROM python:3.4-onbuild

ENV PROXY_BASE_URL="docker.marb.ec"

CMD [ "python" , "./main.py" ]
