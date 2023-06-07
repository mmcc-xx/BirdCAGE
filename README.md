# [See it in action](http://demo.birdcage.rocks/)
This demo deployment is listening in to the [Cornell Lab FeederWatch Cam at Sapsucker Woods](https://www.youtube.com/watch?v=N609loYkFJo)
and proving real time identification of the birds it hears.

# [Install it yourself](https://github.com/mmcc-xx/BirdCAGE/wiki)

![BirdCAGE Screenshot](birdcage.JPG)

# Newest stuff
(listed newest first)
- I just pushed new back end and front end images that provide a more robust mechanism for restarting tasks, and therefore
loading preference and stream definition changes. More robust here means "doesn't break everyone's installs"
- Added installation and usage documentation in the Wiki
- Made it so you don't have the re-start the app for preferences or stream settings changes. You'll see a new button on both of those
pages. Behind the scenes it stops and restarts the recording and analysis tasks. If you happen to hit that button just as a recording has begun, it could take up
to the length of your recording length setting to restart.
- Pushed an image for V2.4 of the model for amd64 - arm64 will be done in a couple hours. New model is supposed to be more
better (see the BirdNET-Analyzer repo for infomation) but it is definitely more slower. So V2.3 is still there under the 
same image name, the new model is at mmcc73/birdnetserver2.4:latest and mmcc73/birdnetserver2.4_arm64:latest. This has been noted in the docker-compose file
- Added annual report. Also, BirdNET released a new model - I need to look into what it will take to pick that up.

# BirdCAGE
BirdCAGE is an application for monitoring the bird songs in audio streams. Security cameras often provide
rtsp and rtmp streams that contain both video and audio. Feed the audio into BirdCAGE and see what sorts of birds are hanging around.

BirdCAGE was strongly inspired by BirdNET-Pi, but with the constraints of running in a Rasberry Pi removed. It utilizes
a slightly patched version of the analysis server provided by the BirdNET-Analyzer project. 

BirdCAGE is written in Python and was designed to be containerizable. It utilizes a separate back end and front end application.
The back end application records streams, calls the analysis server, stores results, and serves as an API server for the front end
application. The front end provides the UI. The back end application uses celery to spin up separate tasks for stream recording
and analyzing and analysis. A Redis container is used to coordinate the tasks.

This is early days. Chances are things will break. Let me know what's broke in the Discussions or in an Issue or an angry
letter or whatever.

## To Do
- I'm planning to work on a "sattelite recorder" based on the ESP32 platform. It'll probably need a different interface to upload audio
to avoid interference between the audio and WiFi.
- Somehow integrate with the video based bird identification app [WhosAtMyFeeder](https://github.com/mmcc-xx/WhosAtMyFeeder)
- User requested enhancements - request away!