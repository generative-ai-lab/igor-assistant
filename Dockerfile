# Separate "build" image
FROM python:3.11-slim-bullseye as compile-image
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# "Run" image
FROM python:3.11-slim-bullseye
COPY --from=compile-image /opt/venv /opt/venv
# RUN apt-get update &&\
#     apt-get install -y ffmpeg &&\
#     rm -rf /var/lib/apt/lists/*
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app/assistant
# COPY . /app/igor_assistant
CMD ["python", "-m", "bot"]
