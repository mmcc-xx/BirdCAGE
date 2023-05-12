# BirdCAGE
I'm working on making BirdNET-Analyzer and BirdNET-Pi more container friendly - hence BirdCAGE.

The BirdNET-Analyze directory contains some "patches" to make to BirdNET-Analyzer so it will provide an analysis API over HTTP, and to run a server that provides that API in a container.

The BirdNET-Pi contains changes to allow it to use that API. This won't work unless you have the above server going.

## Here's what you're gonna do
- Install BirdNET-Pi somewhere. There are directions in the Dicussions area of the BirdNET-Pi repo for getting it installed in a Debian VM in case you aren't down with the whole Pi thing.
- Go into the BirdNET-Analyzer directory. Do what it says there.
- Go into the BirdNET-Pi directory. Do what it says there.

## To Do
- While this seems to be working on my machine, but isn't very robust... the client does not handle the server disappearing very well. So that needs fixing.
- Get the rest of the BirdNET-Pi app running in one or more containers
