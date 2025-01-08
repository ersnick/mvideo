FROM python:3.10-slim

WORKDIR /parser_worker

COPY . /parser_worker

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "parser_worker.py"]