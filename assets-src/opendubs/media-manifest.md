# OpenDubs media manifest

Site-ready media made from Eric's originals in Downloads (2026-10-22). Everything below is in `src/projects/opendubs/images/`. None of it is placed in an entry yet.

How the files were made:
- All metadata was stripped: no EXIF, GPS, dates or device tags. Clips were encoded with `-map_metadata -1`.
- Photos: JPEG, at most 2000 px on the long side, under 1 MB.
- Clips: H.264, 1280 px on the long side (portrait clips stay portrait), `-crf 28 -preset slow -pix_fmt yuv420p -movflags +faststart`, silent unless noted.
- Every clip has a poster: a `.jpg` with the same name.
- The script (`process.py`, kept locally, not in the repo) ran in the existing `achilles-v2-py` Docker image, so nothing new was installed.

How to read the table:
- **Date:** comes from the file's own metadata when it had any. "No metadata" means the original had no date. IMG numbers suggest a rough order: IMG_1345.MOV is dated 2026-08-06, so IMG_1332–1344 are likely early August, not February.
- **Whose work:**
  - "Mine": per Eric, any footage of an arm moving runs on his controller.
  - "Demo routine on my infra": the motion was choreographed by someone else and runs on the arm infrastructure Eric built.
  - "?" means Eric should confirm.
- **Taken by:** "Unknown" means nobody has said who took it. Eric to confirm.

| File | Original | Entry | Date taken | What it shows | Whose work | Taken by | People visible | Draft alt text |
|---|---|---|---|---|---|---|---|---|
| bringup-cad.jpg | image (3).png | bringup | No metadata | CAD render of the full rover base: frame, mecanum wheels, panels, e-stop | ? (CAD author unknown) | Screenshot | None | CAD render of the OpenDubs rover base with mecanum wheels and an e-stop on the top deck |
| bringup-base-frame.jpg | IMG_1332.jpg | bringup | No metadata (IMG # suggests ~Aug 2026) | Top-down view of the bare base frame, wiring and terminal blocks in progress | Mine? | Unknown | None | Top-down view of the aluminum base frame with wiring and terminal blocks in progress |
| bringup-wiring-top.jpg | IMG_1333.jpg | bringup | No metadata (~Aug 2026?) | Base from above with display, wiring and charger | Mine? | Unknown | None | The base from above with its wiring, a small display and power electronics in place |
| bringup-estop.jpg | IMG_1342.jpg | bringup | No metadata (~Aug 2026?) | E-stop handle in a yellow printed mount, wired up | Mine? | Unknown | None | Emergency-stop handle in a yellow 3D-printed mount, wired into the base |
| bringup-battery.jpg | IMG_1343.jpg | bringup | No metadata (~Aug 2026?) | 51.2 V LiFePO4 battery mounted in the base frame | Mine? | Unknown | None | 51.2 V LiFePO4 battery mounted inside the base frame |
| bringup-display-mount.jpg | IMG_1344.jpg | bringup | No metadata (~Aug 2026?) | Status display in yellow printed brackets on the frame | Mine? | Unknown | None | Status display held in yellow 3D-printed brackets on the base frame |
| bringup-first-drive.mp4 (+ .jpg) | IMG_1633.mov, 0–12.9 s | bringup | 2026-08-28 | Rover base driving down a hallway | Mine? | Unknown | One person walking (from behind) | The rover base driving down a hallway while a person walks ahead of it |
| bringup-full-robot-drive.mp4 (+ .jpg) | IMG_1767.MOV, 0–18.4 s (full) | bringup (or a later entry: the arms are already on) | 2026-09-10 | The full robot with arms driving and turning in the lab | Mine? | Unknown | One seated person (from behind) | The full robot, arms mounted, driving and turning in the lab |
| optical-flow-sensor-mount.jpg | IMG_8964.jpg | optical-flow | No metadata | Optical-flow sensor in a black printed mount | Mine? | Unknown | None | Optical-flow sensor in a black 3D-printed mount |
| optical-flow-mocap-arena.jpg | 20260602_124558.jpg | optical-flow? | 2026-06-02 (from filename, not March) | Mocap arena with wooden blocks laid out as a course | ? | Unknown | None | Motion-capture arena with wooden blocks laid out as a course |
| impedance-control-hand-guided.mp4 (+ .jpg) | IMG_3136.MOV, 0–20 s | impedance-control | 2026-06-26 | A hand pushing and guiding one compliant arm; it gives way and holds | Mine | Unknown (looks like Eric's POV) | A hand/forearm only | A hand pushes and guides a robot arm, which yields and holds its new pose |
| impedance-control-wrist.mp4 (+ .jpg) | IMG_3137.MOV, 0–16 s | impedance-control | 2026-06-26 | Close-up of a hand moving the arm's wrist and gripper | Mine | Unknown (looks like Eric's POV) | A hand/forearm only | Close-up of a hand moving the arm's wrist and gripper by hand |
| impedance-control-trajectory.mp4 (+ .jpg) | IMG_2122.MOV, 3–18 s | impedance-control (trajectory following?) | 2026-10-08 | One arm repeatedly reaching out and back along a path | Mine? Confirm it's a trajectory, not a routine | Unknown | None | One robot arm repeatedly reaches out and back along a set path |
| impedance-control-holding-pose.jpg | IMG_1765.MOV, still at 12 s | impedance-control? | 2026-09-10 | Both arms held in a pose while the head moves | Mine? Confirm it's gravity compensation | Unknown | None | Both robot arms held still in a pose beneath the robot's face screen |
| teleop-quest-both-arms.mp4 (+ .jpg) | 20260924_153019.mp4, 203–221 s | teleop (from the Winbond demo) | 2026-09-24 | Eric in a Quest headset; the arms follow his motion in front of the visitors | Mine | Unknown (a visitor or teammate) | Eric (headset); about 10 Winbond visitors | Eric, wearing a Quest headset, teleoperates both arms as visitors watch |
| arm-group-bimanual.jpg | IMG_1760.jpg | arm-group | No metadata (IMG # near Sep 2026 clips) | Both arms on the column with the face screen, in the lab | Mine? | Unknown | None | Two robot arms mounted on a central column under a face screen |
| arm-group-can-wiring.jpg | IMG_1761.jpg | arm-group | No metadata | Two-channel CAN FD adapter and arm wiring | Mine? | Unknown | None | A two-channel CAN FD adapter wired into the arm harness |
| arm-group-front.jpg | 1000016594.mp4, still at 30 s | arm-group | 2026-09-26 | Front view of both arms and the face screen | Mine? | Unknown | None | Front view of the robot's two arms and face screen |
| parallel-arms-reach-out.mp4 (+ .jpg) | IMG_1942.MOV, 3–20 s | parallel-arms | 2026-09-22 (the Fauna visit day) | Both arms extend out to the sides at the same time | Mine? Could be a demo routine on my infra | Unknown | Feet of the person filming | Both robot arms reach out to the sides at the same time |
| parallel-arms-raised.mp4 (+ .jpg) | IMG_1944.MOV, 22–39 s | parallel-arms (or winbond-fauna-demos) | 2026-09-22 | Both arms raised wide, moving together, dance-like | Likely a demo routine on my infra (confirm) | Unknown | None | Both robot arms lift high and wide, moving together |
| winbond-demo-talk.mp4 (+ .jpg) | 20260924_153019.mp4, 28–46 s, **with audio** | winbond-fauna-demos | 2026-09-24 | Eric presenting the robot to the Winbond group (audio: Eric speaking) | Mine (talk); robot shown standing | Unknown | Eric; about 20 Winbond visitors | Eric presents the OpenDubs robot to a group of Winbond visitors |
| winbond-demo-talk-silent.mp4 (+ .jpg) | Same as above, silent | winbond-fauna-demos | 2026-09-24 | Silent version of the clip above | Same | Unknown | Same | Same |
| fauna-lab-visit.jpg | IMG_1937.jpg | winbond-fauna-demos | No metadata (thought to be Fauna, Sep 22) | Visitors standing around robots in the lab | n/a | Unknown | About 8 people, none centered | Visitors gather around robots in the lab |
| arcs-portrait.jpg | ARCS-20261017-IMG_9470.jpg | arcs-demo | 2026-10-17 | Eric and one other person standing with the robot at ARCS (full frame of the crop already used as arcs-eric-robot.jpg) | n/a | **Jason J. Kim Photography** (credit needed) | Eric; one other person (name unknown) | Eric and a colleague stand on either side of the OpenDubs robot at ARCS Night to Ignite Science |
| arcs-dance.mp4 (+ .jpg) | monster_mash_face.mp4, 16–34 s, silent | arcs-demo | No metadata | **Simulation** render of the Monster Mash routine: the arm pose on the left, the face expressions on the right | Demo routine on my infra (choreography not Eric's) | Rendered | None | Simulation of the robot's Monster Mash dance, with its face expressions beside it |
| cover-with-dubs.jpg | IMG_2188.jpg | (cover candidate) | No metadata (~Oct 2026) | The full robot by a window with Dubs, the UW husky mascot | n/a | Unknown | None (dog only) | The OpenDubs robot standing beside Dubs, the University of Washington husky mascot |
| opendubs-architecture.jpg | OpenDubsV2.png | (any; overview?) | No metadata | System architecture block diagram (downscaled from 8408 px, so small text may be hard to read) | ? (author unknown) | n/a | None | OpenDubs system architecture block diagram |

## Made but not committed

- **arcs-dance-with-audio.mp4:** the same excerpt with the Monster Mash audio. The song is copyrighted, so it's kept out of the public repo for now. Eric decides whether it goes up.
- **arcs-group (IMG_1545.jpeg):** already in the repo as `arcs-team.jpg`, from the same photo. That photo was taken by the event organizer on Daphne's phone; please confirm. It shows 4 people with the robot.

## Looked at and skipped

- **IMG_1768.MOV:** near-duplicate of IMG_1767.
- **IMG_1925.MOV:** both arms, but the motion is small. IMG_1942 and IMG_1944 show parallel motion better.
- **20260924_153019 (1).mp4:** same size and length as the Winbond video, treated as a copy.
- **ARCS-20261017-IMG_9470 (1).jpg and the 788 MB zip:** copies of the portrait.
- **IMG_1341.jpg:** a charger lying on the carpet.
- **IMG_1606.png:** a person, not the robot, is the subject.
- **IMG_1939.jpg:** Fauna's humanoid, not our robot.
- **IMG_2165.MOV:** robot in a t-shirt with a hand on the floor; no clear point.
- **leash_720p.mp4:** sim render with no matching entry.
- **paddle_set_v4_720p.mp4:** sim render with a stock kayak photo on the face (third-party image).
- **Lift, UI and head clips that match no entry:** IMG_1345, IMG_1738, IMG_1740, IMG_1741, IMG_1752, Video Clip 2026-08-13 14_14_21 and 14_16_04.
- **Lidar-entry screenshots:** image (1).png (dashboard LIDAR tab), image (2).png (floor-plan path) and map_screenshot.png (SLAM map). That entry uses sim, and the brief asked for photos only.
- **Dashboard screens:** image (8), (9) and (10).png. Unsure whose work.
- **Not OpenDubs or third-party:**
  - image.png and Screenshot 2026-10-09 182056.png (ARUW/LD19)
  - image (4) and (5).png (tracked-robot concept)
  - image (6) and (7).png (boat hull)
  - image (11).png (motor datasheet)
- **Unsure what they show:**
  - IMG_1672.jpg: hand holding a yellow printed bracket over the base. A flow-sensor mount?
  - IMG_8909.jpg: hand-drawn wiring sketch.
