# first stage
FROM alpine:3.15

RUN apt-get update

RUN yes | apt-get install python3-dev build-essential

RUN pip install -U --upgrade pip

RUN pip install requirements.txt

EXPOSE 5000

# make sure you include the -u flag to have our stdout logged
CMD ["python", "bot/bot.py"]

