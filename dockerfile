# first stage
FROM python:3.10-onbuild

RUN apt-get update

RUN yes | apt-get install python3-dev build-essential

RUN pip install -U --upgrade pip

RUN pip install requirements.txt

EXPOSE 5000

# make sure you include the -u flag to have our stdout logged
CMD ["python", "bot/bot.py"]

