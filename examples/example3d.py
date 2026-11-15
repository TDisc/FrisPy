import math

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons

from frispy import Disc
from frispy import Discs

fig = plt.figure()
ax = fig.add_subplot(projection='3d')
ax.set_xlim3d(0,150)
ax.set_ylim3d(-75, 75)
ax.set_zlim3d(0, 50) # Exaggerate height by 3x to help visualisation.

# Remove the grid and add the 'ground'
ax.grid(False)
ax.set_xticks([])
ax.set_yticks([])
ax.set_zticks([])
ax.set_xticklabels([])
ax.set_yticklabels([])
ax.set_zticklabels([])
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.set_pane_color((36.0 / 255, 255.0 / 255, 133.0 / 255, 0.3))

# Widget position is defined by [left, bottom, width, height] in percentages of the screen size.
hyzer_ax = plt.axes([0.1, 0.1, 0.5, 0.03])
v_ax = plt.axes([0.1, 0.15, 0.5, 0.03])
hyser_slider = Slider(hyzer_ax, 'Hyzer', -90.0, 90.0, valinit=0.0)
v_slider = Slider(v_ax, 'Velocity', 0.0, 50.0, valinit=25.0)
select_disc_ax = plt.axes([0.7, 0.025, 0.2, 0.15])
select_disc_button = RadioButtons(select_disc_ax, ('wraith', 'ultrastar', 'destroyer'))

# change these params to see different flights
model = Discs.wraith
v = 25 # 25 m/s is about 56 mph
rot = -v / model.diameter  # This is an advance rate of 0.5 which is common (radians per sec)
uphill_angle = 10 # velocity points 10 degrees above the horizon
nose_up = 0 # 0 degrees nose down
hyzer = 15 # 15 degrees hyzer

disc = Disc(model, {"vx": math.cos(uphill_angle * math.pi / 180) * v, "dgamma": rot, "vz": math.sin(uphill_angle * math.pi / 180) * v, "nose_up": nose_up, "hyzer": hyzer})
result = disc.compute_trajectory(15.0, **{"max_step": .1})
times = result.times
t, x, y, z = result.times, result.x, result.y, result.z

graph = ax.scatter3D(x, y, z, color='b')

def compute(v, hyzer, model):
    disc = Disc(model, {"vx": math.cos(uphill_angle * math.pi / 180) * v, "dgamma": rot, "vz": math.sin(uphill_angle * math.pi / 180) * v, "nose_up": nose_up, "hyzer": hyzer})
    result = disc.compute_trajectory(15.0, **{"max_step": .1})
    times = result.times
    t, x, y, z = result.times, result.x, result.y, result.z
    return t, x, y, z

def draw(x, y, z):
    global graph
    graph.remove()
    graph = ax.scatter3D(x, y, z, color='b')
    fig.canvas.draw()
    fig.canvas.flush_events()

def update(_):
    global v, hyzer, model
    hyzer = hyser_slider.val
    v = v_slider.val
    t, x, y, z = compute(v, hyzer, model)
    draw(x, y, z)

def select_disc(label):
    global model
    model = Discs.from_string(label)
    t, x, y, z = compute(v, hyzer, model)
    draw(x, y, z)

hyser_slider.on_changed(update)
v_slider.on_changed(update)
select_disc_button.on_clicked(select_disc)

plt.show()
