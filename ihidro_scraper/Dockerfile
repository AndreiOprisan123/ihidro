FROM python:3.11-alpine

RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    && pip3 install selenium

COPY entrypoint.py /entrypoint.py

CMD ["python3", "/entrypoint.py"]
