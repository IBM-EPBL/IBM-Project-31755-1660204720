FROM python:3.10
WORKDIR /app
ADD . /app
COPY requirements.txt /app
RUN python3 -m pip install -r requirements.txt
EXPOSE 3001
CMD ["python","app.py","--host", "0.0.0.0"]