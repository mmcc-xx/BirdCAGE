# Build from Python 3.8 slim
FROM python:3.8-slim

# Install required packages while keeping the image small
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
# Install Python packages from requirements.txt
RUN pip install -r requirements.txt

# Import all scripts
COPY . ./

# Add entry point to run the script
ENTRYPOINT [ "python3" ]
CMD [ "server.py" ]
