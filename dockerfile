FROM python:3.8-slim

RUN apt update && \
    apt install --no-install-recommends -y build-essential gcc && \
    apt clean && rm -rf /var/lib/apt/lists/*

COPY ./bot /src
COPY ./requirements.txt /requirements.txt

RUN pip3 install --no-cache-dir --user -r requirements.txt

EXPOSE 5000

# include the -u flag to have our stdout logged
CMD ["python", "-u", "src/bot.py"]

