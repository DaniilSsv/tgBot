FROM python:3.10-slim

WORKDIR /

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_CHAT_ID=""

CMD [ "python", "main.py" ]