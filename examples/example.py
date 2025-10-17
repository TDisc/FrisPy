import math

import matplotlib.pyplot as plt

from frispy import Disc
from frispy import Discs

# change these params to see different flights
model = Discs.wraith
v = 25 # 25 m/s is about 56 mph
rot = -v / model.diameter  # This is an advance rate of 0.5 which is common (radians per sec)
uphill_angle = 10 # velocity points 10 degrees above the horizon
nose_up = 0 # 0 degrees nose down
hyzer = 15 # 15 degrees hyzer

disc = Disc(model, {"vx": math.cos(uphill_angle * math.pi / 180) * v, "dgamma": rot, "vz": math.sin(uphill_angle * math.pi / 180) * v, "nose_up": nose_up, "hyzer": hyzer})

result = disc.compute_trajectory(15.0, **{"max_step": .2})
times = result.times
t, x, y, z = result.times, result.x, result.y, result.z

plt.plot(x, y)
plt.plot(x, z)

plt.show()
