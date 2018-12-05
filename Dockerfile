FROM python:3.7


MAINTAINER Nitish Goyal "nitish.goyal@phonepe.com"

# Create app directory
WORKDIR /app
COPY . /app

RUN pip3 install requests
RUN pip3 install simplejson

EXPOSE 8080
CMD [ "python3", "./marathon-autoscale.py" ]