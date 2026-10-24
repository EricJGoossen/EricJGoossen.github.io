---
title: Checking the Odin's new mount
date: 2026-10-09 18:00:00
skillTags: [State estimation]
---
{# Placeholder: Eric to confirm. From Eric's Oct 9 test report (Odin1 new-mount sanity check) and his Slack message (Oct 24). The photo is from the Odin's own camera on the new mount (Eric's screenshot, sent Oct 24). #}
{% row "images/odin-camera-view.jpg", "Fisheye view from the sentry's sensor: a cluttered lab with boxes and a chair, a person sitting on the floor with a laptop, and the robot's own black chassis along the bottom", { caption: "The view from the Odin's camera on the new mount, with the robot itself along the bottom." } %}
When the Odin moved to a new mount, I checked it against the old one using the data from the LD19 tests. There was no mocap that day, so the numbers are less precise, but they point the same way. At rest nothing changed: the IMU noise is the same (about 2.9 mg and 111 mdps), pose jitter is about 1 mm and drift under 2 mm a minute, so the mount is rigid. It is a bit more occluded: 23% of the Odin's directions now get no return, against 17.5% before, so about 6% more of its view is lost, and it sits tilted 1.4° differently. While moving, position drift matched the old mount, 5 cm over 25 m (0.2%). Heading drift read higher, 1.6° against 0.1–0.4°, but the only reference was the 2D lidar, which compounds the errors of the two sensors.
{% endrow %}
