FROM python:3.9-alpine

WORKDIR /usr/src/app

RUN apk update && apk add --no-cache g++ gcc libxslt-dev tzdata

RUN pip install --no-cache-dir ytmusicapi lxml requests pymongo schedule

RUN apk add bash

COPY . .

CMD ["python", "-u", "ytmusicHousekeeping.py"]
