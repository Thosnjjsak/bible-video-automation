FROM python:3.11-slim
RUN apt-get update && apt-get install -y imagemagick ffmpeg && rm -rf /var/lib/apt/lists/*
# This uses a wildcard (*) to find the policy file in any ImageMagick version folder
RUN sed -i 's/domain="path" rights="none" pattern="@\*"/domain="path" rights="read|write" pattern="@\*"/g' /etc/ImageMagick*/policy.xml
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
