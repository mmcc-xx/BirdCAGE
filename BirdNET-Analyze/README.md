# Here's what you're gonna do...

- clone the BirdNET-Analyzer repo https://github.com/kahst/BirdNET-Analyzer
- Replace their server.py with the one in this directory
- Replace their Dockerfile with the one in this directory
- Copy in the docker-compose.yml file from this directory. Edit to your liking.
- Build the image with `docker build -t birdnetserver .`
- Start that bad boy up with `docker-compose up -d`
