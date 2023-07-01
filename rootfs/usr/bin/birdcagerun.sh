#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Community Add-on: Birdcage
# Runs example1 script
# ==============================================================================

bashio::log.info "Running docker-compose pull the up"

PROJECT_NAME="birdcage"  # Replace with your desired project name

# Pull the latest images for the services defined in the docker-compose.yml file
docker-compose -p "$PROJECT_NAME" -f /usr/src/addon/docker-compose.yml pull

# Start the add-on using docker-compose with the specified project name and YAML file
docker-compose -p "$PROJECT_NAME" -f /usr/src/addon/docker-compose.yml up -d

bashio::log.info "Getting logs"

# Function to print logs of all containers
print_container_logs() {
  bashio::log.info "Printing logs for all containers:"
  docker-compose -p "$PROJECT_NAME" -f /usr/src/addon/docker-compose.yml logs -f > >(while IFS= read -r line; do bashio::log.info "${line}"; done)
}

# Print logs for all containers
print_container_logs

# Keep the script running to keep the container alive
tail -f /dev/null