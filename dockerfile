# first stage
FROM python:3.8-slim

RUN apt update && \
    apt install --no-install-recommends -y build-essential gcc && \
    apt clean && rm -rf /var/lib/apt/lists/*
COPY ./requirements.txt /requirements.txt
COPY ./bot /src

RUN pip3 install --no-cache-dir --user -r requirements.txt

EXPOSE 5000
# CMD ['python3', '/src/app.py']

# make sure you include the -u flag to have our stdout logged
CMD ["python", "-u", "src/bot.py"]

