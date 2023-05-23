# A change was recently made in the BirdNET-Analyzer repo that broke the integration.
Later today (May 23) I'll push a known good image and change the docker-compose in the main directory to use it.

So don't bother doing the stuff below. It won't work.

# Here's what you're gonna do...

- clone the BirdNET-Analyzer repo https://github.com/kahst/BirdNET-Analyzer
- Replace their server.py with the one in this directory
- Replace their analyze.py with the one in this directory
- Replace their Dockerfile with the one in this directory
- Copy in the docker-compose.yml file from this directory. Edit to your liking.
- Build the image with `docker build -t birdnetserver .`
- Start that bad boy up with `docker-compose up -d`
