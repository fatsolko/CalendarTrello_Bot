# first stage
FROM python:buster-slim

RUN apk update and apk add

RUN apt-get update

RUN yes | apt-get install python3-dev build-essential

RUN pip install -U --upgrade pip

RUN pip install --no-cache-dir --user -r requirements.txt

EXPOSE 5000

# make sure you include the -u flag to have our stdout logged
CMD ["python", "bot/bot.py"]

