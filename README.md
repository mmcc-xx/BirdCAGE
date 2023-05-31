# [See it in action](http://demo.birdcage.rocks/)
This demo deployment is listening in to the [Cornell Lab FeederWatch Cam at Sapsucker Woods](https://www.youtube.com/watch?v=N609loYkFJo)
and proving real time identification of the birds it hears.

![BirdCAGE Screenshot](birdcage.JPG)

# Newest stuff
(listed newest first)
- I have a highly credible report of BirdCAGE successfully runnong on a Raspberry Pi 4! This particular Pi was running the latest
DietPi OS, but it _should_ work on any 64 bit Linux. It _should_ also work on other arm64 based machines. Please try it out and if it
doesn't work, open an issue. If it does work, please post in the discussions forum.
- Added a preference for how long to retain recordings, and once a day delete all recordings older than that. I keep the database
entries as they are pretty tiny.
- Made the grid on the index page a little nicer, especially for small screens. Future hours aren't show, and the column and row headers are
"sticky" when you scroll around.
- Added notifications via Apprise. You'll see a new pick under the Settings window for Notifications Settings. Put in URLs
for up to 3 notifications services per the Apprise documentation, and associate those services with the Log, Record and Alert
detection levels defined in the Filter Settings. I tried MQTT and email via gmail and both worked. Note: this does not replace
a real MQTT interface which I'm planning to work on real soon now.
- Added locale support for results. The UI is still just english, but you can get back common names in other language. See
the Locale setting in Preferences. After you change it, restart the application.

# BirdCAGE
BirdCAGE is an application for monitoring the bird songs in audio streams. Security cameras often provide
rtsp and rtmp streams that contain both video and audio. Feed the audio into BirdCAGE and see what sorts of birds are hanging around.

BirdCAGE was strongly inspired by BirdNET-Pi, but with the constraints of running in a Rasberry Pi removed. It utilizes
a slightly patched version of the analysis server provided by the BirdNET-Analyzer project. 

BirdCAGE is written in Python and was designed to be containerizable. It utilizes a separate back end and front end application.
The back end application records streams, calls the analysis server, stores results, and serves as an API server for the front end
application. The front end provides the UI. The back end application uses celery to spin up separate tasks for stream recording
and analyzing and analysis. A Redis container is used to coordinate the tasks.

## Here's what you're gonna do
- Assuming you are using docker-compose, create a new directory on your server for the application. Put the docker-compose.yml
file from this repo in there. Create detections and db directories in there as well.
- Edit the docker-compose.yml file to meet your needs.
    - If you just want to view the UI from your intranet via IP addresses,
all you should have to do is replace 192.168.1.75 (in 3 places) with the IP address of your server.
    - If you want to be able to access it
from the internet, use your reverse proxy to give names to both the front end and back end (birdcage.yourdomain.com and
birdcageapi.yourdomain.com). Add the front end url to CORS_ORIGINS (e.g. CORS_ORIGINS: http://192.168.1.75:7008,http://birdcage.yourdomain.com)
and use back end name for API_SERVER_URL (e.g. API_SERVER_URL: http://birdcageapi.yourdomain.com).
    - ANALYZE_SERVER should the IP address of your server, and ANALYZE_PORT should be the port that is being mapped. 
to 8080 in the birdnetserver service section. (In theory interactions with the birdnetserver could all be on the virtual 
network. I need to try that out. For now, use a LAN address)
- docker-compose up
- From the Web UI go to Stream Settings and add a stream. The user name is 'admin and default password is 'birdcage'. 
The Name field is for however you want the stream identified in the
UI. Address is the full url of the stream from your source (try opening it in VLC to make sure it works if you aren't sure).
Protocol is http, rtmp, or rtsp. Transport is TCP or UDP. This is only important for rtsp because it can use either one.
- Go to Preferences and set your latitude and longitude and tweak other settings. The default password is 'birdcage'. 
If you live in Topeka, Kansas you are
in luck: your latitude and longitude are already set.
- Consider changing the default password. Or don't.
- Did the above not work?
    - See if you can go to whatever you set as your API_SERVER_URL in your browser. You should see a (very incomplete) UI of API documentation.
    If not, the back end / API server is not exposed to the network correctly or the docket-compose file isn't configured correctly. Or both.
    - If that works, go back to the Preferences page, hit F12 and see if there are any client side scripting errors. All of the API
    calls are done in client side scriping in the browser to keep things snappy. If you are accessing the Web UI through a name via a reverse
    proxy, that name needs to be added to the CORS_ORIGINS environment variable in docker-compose.yml, you need to set a name for the back end/API server, and that name
    needs to be specified in the API_SERVER_URL environment variable in docker-compose.yml.
- Kill the BirdCAGE application (control C or docker-compose down). I don't have nice way to start recording from new streams yet.
- docker-compose up one more time. It should now start recording and analyzing

This is early days. Chances are things will break. Let me know what's broke in the Discussions or in an Issue or an angry
letter or whatever.

## To Do
- Handle changing streams and preferences without having to kill the app.
- I'm planning to work on a "sattelite recorder" based on the ESP32 platform. It'll probably need a different interface to upload audio
to avoid interference between the audio and WiFi.
- Reporting
- MQTT interface
