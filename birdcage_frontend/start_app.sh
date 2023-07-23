#!/bin/bash

#
# Gunicorn won't pass environment variables by default,
# so pass anything we might be specifying in docker-compose.
#
# SCRIPT_NAME is a wsgi convenience feature that gunicorn
# uses to tell Flask that the application may live in a subfolder.
#

gunicorn --bind 0.0.0.0:${WEBUI_PORT} \
	-e API_SERVER_URL="${API_SERVER_URL}" \
	-e SCRIPT_NAME="${SCRIPT_NAME}" \
	-e TITLE_LINK="${TITLE_LINK}" \
	-e TITLE_TEXT="${TITLE_TEXT}" \
	webui:app
	
