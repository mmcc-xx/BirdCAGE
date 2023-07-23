# [See it in action](http://demo.birdcage.rocks/)
This demo deployment is listening in to the [Cornell Lab FeederWatch Cam at Sapsucker Woods](https://www.youtube.com/watch?v=N609loYkFJo)
and proving real time identification of the birds it hears.

# [Install it yourself](https://github.com/mmcc-xx/BirdCAGE/wiki)

![BirdCAGE Screenshot](birdcage.JPG)

# Newest stuff
(listed newest first)
- Now setting the "retain" flag on MQTT publications. The payload also include the expected occurrence score for the species
- Now storing spectograms to disk the first time they are generated, and deleting them when the recordings get cleaned up.
- Added an App Health report that. I also put try/catch blocks around the main loops in the worker tasks so if there's an
exception it should just try again. If you are looking at your detections and things look funny, take a look at that report
and see if it indicates that exceptions are occurring. This will not tell you if your camera is offline, though it probably
should.
- Added support for PulseAudio input, meaning you can plug a mic into your soundcard and use that for audio. It wasn't that
hard to add support for it in the code, but it kind of is a pain to set up. The intersection of Linux and audio inevitably
involves pain. There's a new environment variable in the docker-compose file. Here's how you make it go:
https://github.com/mmcc-xx/BirdCAGE/wiki/PulseAudio If there's need for ALSA support please let me know
- Added some additional debug output around db calls, and upped some timeouts. At least one user is getting database lock
problems and I'm trying to get to the bottom of that.
- I just pushed new back end and front end images that provide a more robust mechanism for restarting tasks, and therefore
loading preference and stream definition changes. More robust here means "doesn't break everyone's installs"


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
- I'm planning to work on a "satelite recorder" based on the ESP32 platform. It'll probably need a different interface to upload audio
to avoid interference between the audio and WiFi.
- Somehow integrate with the video based bird identification app [WhosAtMyFeeder](https://github.com/mmcc-xx/WhosAtMyFeeder)
- User requested enhancements - request away!

# Installing as an addon for home assistant
Word of warning, this will use the concept of docker out of docker. HA doesn't nativly (yet) support docker-compose. So this is a work around. The addon needs access to the docker api, thus the score will be 1 and protection will have to be removed.
It will also generate an 'unsupport system' error because you are creating containers that aren't supervised. If updating or submitting issues to the HA dev team, stop the addon and restart HA.

## How it works
Because HA doesn't support docker-compose, this addons is mainly a hack. All it does is spin up a container with docker / docker_compose installed. Then uses the S6 overlay to issue a docker-compose pull the up command as a start script. It also funnels the logs to bashio.
On stopping the addon, the kill timeout is set to 60 seconds to allow the docker-compose down script to properly finish.

## How to install
- Using the samba (or ssh) addon, connect to the addon folder and create a new folder called birdcage.
- Clone the repo.
- Modify the new docker-compose.yml file with host IP, uncomment / comment lines for the HA addon.
- You shouldn't need to modify the webui in the config file. But if you can't connect add the same ip from the docker-compose.yml
- In the share folder (via samba / ssh / file editor) create a folder called 'birdcage' and two subfolders called 'db' and 'detections'.
- Reload addons and it should appear as a local addon, if not check the logs for errors
- You might need to refresh the webpage, once found install the addon and check for errors in the log
- Run the addon
- Voila

## Files
The db and recodings are saved in the share folder. You can sqlite the db and extract for personal analysis.

## Debugging
If it complains or doesn't start after a while (be carefull as it's pulling a couple docker images that are quite large). Use portainer and check whats going on. You can access the bash of the addon container through portainer, and check whats going on. It usally has to do with either ports or the share volumes not being there.

### Todo for HA addon
- Modify docker-compose script to use localhost ip
- See if possible to use sysbox and run as dind without privilage.
- Try building all contaiers with S6 overlay provided by HA and run services through S6