FROM python:3.12-slim

# تثبيت Java + wget
RUN apt-get update && \
    apt-get install -y --no-install-recommends default-jre-headless wget && \
    rm -rf /var/lib/apt/lists/*

# تحميل smali fat jar (النسخة القابلة للتشغيل)
RUN mkdir -p /app/tools && \
    wget -q -O /app/tools/smali.jar \
    "https://github.com/baksmali/smali/releases/download/v3.0.9/smali-3.0.9-fat.jar" && \
    java -jar /app/tools/smali.jar --version

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
