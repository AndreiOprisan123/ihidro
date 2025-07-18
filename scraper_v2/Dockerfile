ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    python3 \
    py3-pip \
    && pip3 install selenium

COPY run.py /run.py

CMD ["python3", "/run.py"]