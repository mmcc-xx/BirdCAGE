# Base image for Home Assistant add-ons with S6 overlay
ARG BUILD_FROM
FROM $BUILD_FROM

# Install dependencies
RUN apk --no-cache add curl

# Install Docker
RUN apk --no-cache add docker

# Install docker-compose
RUN curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose && \
    chmod +x /usr/local/bin/docker-compose


# Copy the add-on files
COPY . /usr/src/addon

# Set the working directory
WORKDIR /usr/src/addon

# Copy S6 overlay files
COPY rootfs /

# Set the entrypoint to start the S6 supervisor
ENTRYPOINT ["/init"]

