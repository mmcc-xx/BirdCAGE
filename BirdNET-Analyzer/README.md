# A change was recently made in the BirdNET-Analyzer repo that broke the integration.
The docker-compose.yml now uses an image that I pushed that I know to work. So, don't bother with
the steps below.

# Here's what you're gonna do...

- clone the BirdNET-Analyzer repo https://github.com/kahst/BirdNET-Analyzer
- Replace their server.py with the one in this directory
- Replace their analyze.py with the one in this directory
- Replace their Dockerfile with the one in this directory
- Copy in the docker-compose.yml file from this directory. Edit to your liking.
- Build the image with `docker build -t birdnetserver .`
- Start that bad boy up with `docker-compose up -d`
