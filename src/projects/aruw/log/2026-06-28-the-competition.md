---
title: The competition and our robots
date: 2026-06-28
info:
  language: C++
  hardware: The engineer, then the sentry
  role: "Software: odometry and path tracking"
  status: 3rd in the 3v3 at the 2026 ARC Championship
links:
  - label: "Robot reveal"
    url: "https://www.youtube.com/watch?v=FGh1yQdJGeM"
  - label: "Championship match"
    url: "https://www.youtube.com/watch?v=PqSzhmRSAZA"
  - label: "ARUW"
    url: "https://aruw.org/"
---
{# Placeholder: Eric to confirm. Eric suggested this entry (Oct 24) and asked to publish it (Oct 25). Dated by the robot reveal's release on YouTube, June 28, 2026 (Eric, Oct 25). From aruw.org (Oct 25): "What is ARC Robotics?" (DJI hosts it; operators drive through an onboard camera; 17 mm and 42 mm projectiles; pressure-sensitive armor plates; take down the robots and/or disarm the base), "Our Robots" (eight robots, a team deathmatch "that resembles paintball and League of Legends", most redesigned every season; the engineer can't launch projectiles and collects minerals to exchange for coins; the sentry is the only fully autonomous robot, a base defender whose base shield drops if it dies or leaves the base, and navigates by its own sensors), "ARUW Achievements" (champions 2020–21 through 2023–24, third in the 1v1, 3v3 and Engineer Challenge in 2024–25) and the RMNA 2025 news post (first Engineer Challenge; RMNA 2026 at Purdue). Best of three: Eric (Oct 24). The match video is titled "ARUW vs RoboGrinder | Match 113 | 3v3 ARC Championship 2026"; the reveal, "ROBOT // REVEAL 2026". Eric (Oct 25): aruw.org is out of date, there are no bases any more, the game is king of the hill around a capture point in the center of the field; in 2026 ARUW was 3rd in the 3v3, 2nd in dart, 3rd in drone, and off the podium in the other events. Photos from Eric's ARUW files (aruw-picks.zip, Oct 25: the Quad, Mar 21, 2026); the full reveal is the YouTube thumbnail under the photos; the card and hero clips are cut from the MP4s Eric sent (Oct 25). #}
{% row "images/fleet-lineup.jpg", "Three of ARUW's 2026 robots side by side on the grass, two with long launcher barrels and the black-shelled sentry on the right, with visitors' legs in the background", { caption: "The sentry (right) and two of our other 2026 robots on the Quad in cherry blossom season.", more: [{ src: "https://www.youtube.com/watch?v=FGh1yQdJGeM", alt: "Our 2026 robot reveal", poster: "images/reveal.jpg" }] } %}
Advanced Robotics at UW competes in ARC, DJI's robotics competition for universities in North America (RoboMaster North America until 2025). Every season the team designs and builds a fleet of eight robots, most of them new ([this year's reveal](https://www.youtube.com/watch?v=FGh1yQdJGeM)), for what the team calls a deathmatch somewhere between paintball and League of Legends. Operators drive their robots through an onboard camera and fire 17 mm and 42 mm projectiles at the pressure-sensitive armor plates on the other team's robots, while fighting king-of-the-hill style for a capture point in the middle of the field, in matches that are each a best of three. The engineer can't shoot: it collects minerals to trade for coins that buy supplies during the match. The sentry is the only fully autonomous robot on the field, finding its own way around and aiming on its own. ARUW won the competition every year from 2021 to 2024. At the 2026 ARC Championship at Purdue we placed third in the 3v3, second in the dart event and third in the drone event; for it I worked on the engineer's odometry and path tracking, and since then I've moved to the sentry's localization and navigation.
{% endrow %}
