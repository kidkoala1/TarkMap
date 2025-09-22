# TarkMap
TarkMap is an unfinished but functional PoC that translates Escape from Tarkov screenshots into a live position on a map image. When you take a screenshot in EFT, the filename encodes your player coordinates and facing quaternion. TarkMap parses that filename, converts it to pixel coordinates, and displays your current position and facing direction on a map in real time.

![example](https://files.catbox.moe/wzlps9.gif)

# Requirements
- Python 3.8+
- [Pillow](https://pypi.org/project/pillow/)
- [Watchdog](https://pypi.org/project/watchdog/)

# Notes
The calibration constants are currently set for customs.png. If you use a different map, you’ll need to provide your own map image and adjust world_to_pixel() accordingly.
On closing the program, you’ll be asked if you want to delete all .png files in your screenshot folder. Be careful this removes all screenshots, not just TarkMap ones.

# How It Works
EFT screenshots contain filenames like:
```
2024-09-12_14-31-09_679.69, 0.00, -272.68_0.0, 0.0, 0.0, 1.0_.png
```
The script extracts the coordinates (x, z) and quaternion (qx, qy, qz, qw).
Coordinates are transformed to map pixel positions using calibration constants in world_to_pixel().
Quaternion is converted to a yaw angle.
The GUI updates a marker + arrow showing your latest screenshot position.

