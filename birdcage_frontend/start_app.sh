#!/bin/bash

gunicorn --bind 0.0.0.0:$WEBUI_PORT webui:app