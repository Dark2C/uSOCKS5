FROM python:3.13-rc-alpine3.18
WORKDIR /app
COPY uproxy.py .
CMD ["python", "uproxy.py"]