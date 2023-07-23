# Use the official Python 3.10 image as the base image
FROM python:3.10

COPY requirements.txt /tmp

# Install Python packages from requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY start_app.sh /
COPY webui.py /
COPY static /static
COPY templates /templates

ENV API_SERVER_URL=http://192.168.1.75 \
    WEBUI_PORT=7008

# Grant execution permission to start_app.sh
RUN chmod +x start_app.sh

# Start the app
CMD ["./start_app.sh"]