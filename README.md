# BirdCAGE
I'm working on making BirdNET-Analyze and BirdNET-Pi more container friendly - hence BirdCAGE.

The BirdNET-Analyze directory contains some "patches" to make to BirdNET-Analyze so it will provide an analysis API over HTTP, and to run a server that provides that API in a container.

The BirdNET-Pi contains changes to allow it to use that API. This won't work unless you have the above server going.
