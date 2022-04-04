# first stage
FROM python:3-onbuild

RUN apt-get update

RUN yes | apt-get install python3-dev build-essential

RUN pip install --upgrade pip

EXPOSE 5000

# make sure you include the -u flag to have our stdout logged
CMD ["python", "application/app.py"]

