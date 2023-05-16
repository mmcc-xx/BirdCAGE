# BirdCAGE Back End Application

This application provides a number of functions:
- It records clips from the configured input streams
- It analyzes the clips with an instance of BirdNET-Analyzer with the patches described in that directory applied
- It stores the results and associated clips
- It provides a bunch of APIs for accessing the results and the recordings

A bunch of dependencies will need to be installed to run this, and I haven't gotten around to documenting them
A bunch of "preferences" will also need to be set. Guess what? I haven't documented those yet either. All in good time.

This application is all python all the time. It uses Celery and Redis to spin on separate tasks for recording each stream
and for analyzing the recordings.

To Do:
- Document
- Containerize
- Provide health indicators of major functions
- Provide controls (pause/restart) of the major functions