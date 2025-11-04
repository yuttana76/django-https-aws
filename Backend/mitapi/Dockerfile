# pull official base image
FROM python:3.10.14
# FROM python:3.9.6-alpine

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
# RUN apk update \
#     && apk add postgresql-dev gcc python3-dev musl-dev

# Add libffi-dev to the list of packages installed with apk
# RUN apk update \
# && apk add --no-cache postgresql-dev gcc python3-dev musl-dev libffi-dev \
# && pip install --upgrade pip


# install dependencies
# RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint.sh
# COPY ./entrypoint.sh .
# RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
# RUN chmod +x /usr/src/app/entrypoint.sh

# copy project
COPY . .

# ENTRYPOINT ["/usr/src/app/entrypoint.sh"]