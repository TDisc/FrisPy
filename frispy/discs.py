#  Copyright (c) 2021 John Carrino

import math
from typing import Optional, TypedDict

from frispy.model import Model

MAX_GLIDE = 5

# constants come from wind tunnel testing done by
# check out "DYNAMICS AND PERFORMANCE OF FLYING DISCS" page 111
class Discs:
    @staticmethod
    def from_string(name: str) -> Optional[Model]:
        if name == "wraith":
            return Discs.wraith
        elif name == "ultrastar":
            return Discs.ultrastar
        elif name == "roc":
            return Discs.roc
        elif name == "flick":
            return Discs.flick
        elif name == "stable_wraith":
            return Discs.stable_wraith
        elif name == "flippy_destroyer":
            return Discs.flippy_destroyer
        elif name == "destroyer":
            return Discs.destroyer
        elif name == "stable_destroyer":
            return Discs.stable_destroyer
        elif name == "beefy_destroyer":
            return Discs.beefy_destroyer
        elif name == "xcal":
            return Discs.xcal
        else:
            return None

    # drag based on speed. This is the minimum drag at 0 lift.  aka PD0
    @staticmethod
    def drag_from_speed(speed: float) -> float:
        return .084 - 0.01355 * math.sqrt(speed)


    # pitching moment at zero angle of attack based on turn
    # ultrastar is about a -3 turn
    # zero pitching at 0 AoA means turn is 0
    # I think tilt is actually 9, 1, +2, 5
    # 0 turn means a lot of things
    @staticmethod
    def cm0_from_turn(t: float) -> float:
        return t * 0.005 - 0.000

    @staticmethod
    def turn_from_cm0(cm0: float) -> float:
        return (cm0 + 0.000) / 0.005

    # fade appears to just be turn value +1, +2, +3, +4 for putters, mids, fairly, distance drivers
    # fade is just a function of cm0 (turn) and lack of cavity to prevent the flat plate effect from
    # happening
    #@staticmethod
    #def cm_from_fade(fade: float) -> float:
    #    return (math.sqrt(fade) + 1) * 0.002 * 180 / math.pi

    # @staticmethod
    # def maxGlideRangeForSpeed(speed: float) -> float:
    #     if speed < 3:
    #         return 3
    #     elif speed > MAX_GLIDE:
    #         return MAX_GLIDE
    #     else:
    #         return speed

    # glide ranges from 0 to 5 for all speeds.
    # if a disc has a ton of dome, then it's a 5
    # lift at zero angle of attack based on glide
    # larger diameter discs have more lift per angle of attack.
    # 0.152/2.29 rads in deg = 3.8 degrees (max glide is 3.8 deg nose down lowest drag)
    # the best way to look at this stat is on a drag graph
    # River might be 7, but that seems to high at 5.3 deg
    @staticmethod
    def cl0FromGlide(glide: float) -> float:
        # percent = glide / Discs.maxGlideRangeForSpeed(speed)
        percent = glide / MAX_GLIDE
        return 0.152 * percent

    # lift change per delta AoA
    # higher speed discs have less lift for the same angle of attack
    # speed 0 is basically defined to be the ultrastar
    @staticmethod
    def dcl_da_from_speed(speed: float) -> float:
        return (0.052 - 0.004 * math.sqrt(speed)) * 180 / math.pi

    class FlightNumbers(TypedDict):
        fade: Optional[float] = None
        glide: float
        speed: float
        turn: float
        weight: float = 0.175
        diameter: float = 0.211

    @staticmethod
    # def from_flight_numbers(speed: float, glide: float, turn: float, fade: float, weight: float = 0.175) -> Model:
    def from_flight_numbers(nums: FlightNumbers) -> Model:
        speed = float(nums["speed"])
        glide = float(nums["glide"])
        turn = float(nums["turn"])
        weight = float(nums.get("weight", 0.175))
        diameter = float(nums.get("diameter", 0.211))
        fade = nums.get("fade")

        speed = min(14, speed)
        speed = max(0, speed)

        # handle up to 2kg for discus
        weight = min(2, weight)
        weight = max(0, weight)

        glide = min(6, glide)
        glide = max(0, glide)

        cl0 = Discs.cl0FromGlide(glide)
        drag = Discs.drag_from_speed(speed)
        pitch0 = Discs.cm0_from_turn(turn)
        # TODO: delete this
        #pitch = Discs.cm_from_fade(fade)
        pitch = 0.3 # this value is not used in model.py
        rim_depth = 0.012
        rim_width = Model.rim_width_from_speed(speed)
        return Model(**{
            "PL0": cl0,  # lift factor at 0 AoA (depends on glide)
            "PLa": 2.29,  # lift factor linear with AoA (0.04 deg -> 2.29 rad) (constant)
            "PD0": drag,  # drag at min lift
            # (.055 at speed 11, .061 speed 5, .067 speed 4, .083 speed 2)
            "PDa": 1.67,  # quadratic with AoA from zero lift point (constant)
            "PTxwz": 0,  # rolling moment related to spin precession?
            "PTy0": pitch0,
            # pitching moment from disc stability at 0 AoA (based on turn of disc, also based on cavity of disc)
            # -0.02 turn -1, -0.007 turn 1, -0.033 turn -2, -0.015 turn 0
            "PTya": pitch,
            # pitching moment from disc stability linear in AoA (0.006 / deg -> 0.343) (based on fade of disc)
            # fade 0 0.002, fade 1 0.004, fade 3  0.006, fade 5 0.008  (per degree not per rad)
            "PTxwx": -6.0e-4,  # dampening factor for wobble (constant) 21.5 -> 3.3 over 1s
            "PTzwz": -2.1e-5,
            # spin down (constant) at 58mph spindown is about 24m/s^2 (3.5% (118.5 -> 114.5) over .82s)
            "I_xx": 6.183E-04 * weight / 0.175,
            "I_zz": 1.231E-03 * weight / 0.175,
            "mass": weight,
            "diameter": diameter,
            "rim_depth": rim_depth,
            "rim_width": rim_width,
            "height": 0.014,
            "speed": speed,
            "turn": turn,
            "fade": fade,
            "glide": glide,
        })

    # condor I_xx is 4-5% higher than 1/2 I_zz
    # I suspect most discs are somewhere around 3-5% off (maybe less for drivers).
    # However, for a known mold we may be able to assume I_xx/I_zz is constant
    # and can be used for calibration.
    # for condor the rotation frequency is 13/12 times the wobble frequency.
    # While in flight accel.x average is about -2.5 m/s^2
    # This corresponds to the rotational spindown
    # accel.x is a sine wave +/- 5 m/s^2  This is equal to the drag on the disc


    ultrastar: Model = Model()
    #"PL0": 0.13,  # lift factor at 0 AoA
    #"PLa": 2.7,  # lift factor linear with AoA
    #"PD0": 0.08,  # drag at 0 lift
    #"PDa": 1.9,  # quadratic with AoA from zero lift point
    ## "PDa": 1.67, # golf discs have less drag per angle of attack;
    #"PTy0": -0.02,  # pitching moment from disc stability at 0 AoA
    #"PTya": 0.13,  # pitching moment from disc stability linear in AoA
    #"PTxwx": -1.08e-3,  # dampening factor for roll
    #"PTzwz": -3.4e-5,  # spin down
    #"PTxwz": 0,  # rolling moment related to spin precession?
    #"I_zz": 0.002352,
    #"I_xx": 0.001219,
    #"mass": 0.175,
    #"diameter": 0.27,
    #"rim_depth": 0.02,
    #"rim_width": 0.007,
    #"height": 0.032,

    wraith: Model = Model(**{
        "PL0": 0.143,  # lift factor at 0 AoA (depends on glide)
        "PLa": 2.29,  # lift factor linear with AoA (0.04 deg -> 2.29 rad) (constant)
        "CD0": 0.055,  # drag at 0 AoA  (based on disc speed)
        # (.055 at speed 11, .061 speed 5, .067 speed 4, .083 speed 2)
        "PDa": 1.67,  # quadratic with AoA from zero lift point (constant)
        "PTxwz": 0,  # rolling moment related to spin precession?
        "PTy0": -0.02,
        # pitching moment from disc stability at 0 AoA (based on turn of disc, also based on cavity of disc)
        # -0.02 turn -1, -0.007 turn 1, -0.033 turn -2, -0.015 turn 0  (per degree not per rad)
        "PTya": 0.343,
        # pitching moment from disc stability linear in AoA (0.006 / deg -> 0.343) (based on fade of disc)
        # fade 0 0.002, fade 1 0.004, fade 3  0.006, fade 5 0.008  (per degree not per rad)
        "PTywy": -1.3e-2,  # dampening factor for pitch (constant)
        "PTxwx": -1.3e-2,  # dampening factor for roll (constant)
        "PTzwz": -3.4e-5,  # spin down (constant)
        "I_xx": 6.183E-04,
        "I_zz": 1.231E-03,
        "mass": 0.175,
        "diameter": 0.211,
        "rim_depth": 0.012,
        "rim_width": 0.0215,
        "height": 0.014,
    })

    stable_wraith: Model = Model(**{
        "PL0": 0.143,  # lift factor at 0 AoA (depends on glide)
        "PLa": 2.29,  # lift factor linear with AoA (0.04 deg -> 2.29 rad) (constant)
        "CD0": 0.055,  # drag at 0 AoA  (based on disc speed)
        # (.055 at speed 11, .061 speed 5, .067 speed 4, .083 speed 2)
        "PDa": 1.67,  # quadratic with AoA from zero lift point (constant)
        "PTxwz": 0,  # rolling moment related to spin precession?
        "PTy0": -0.01, # pitching moment from disc stability at 0 AoA (based on turn of disc, also based on cavity of disc)
        # -0.02 turn -1, -0.007 turn 1, -0.033 turn -2, -0.015 turn 0  (per degree not per rad)
        "PTya": 0.3,
        # pitching moment from disc stability linear in AoA (0.006 / deg -> 0.343 / rad) (based on fade of disc)
        # fade 0 0.002, fade 1 0.004, fade 3  0.006, fade 5 0.008  (per degree not per rad)
        "PTxwx": -1.3e-2,  # dampening factor for roll (constant)
        "PTzwz": -3.4e-5,  # spin down (constant)
        "I_xx": 6.183E-04,
        "I_zz": 1.231E-03,
        "mass": 0.175,
        "diameter": 0.211,
        "rim_depth": 0.012,
        "rim_width": 0.0215,
        "height": 0.014,
    })

    # -3 turn
    flippy_destroyer: Model = Model(**{
        "PL0": 0.16,  # lift factor at 0 AoA (depends on glide) 2 deg Aoa at 58 mph lift was about 8m/s^2   0.8g
        "PLa": 2.29,  # lift factor linear with AoA (0.04 deg -> 2.29 rad) (constant)
        "PD0": 0.035, # keep dropping drag until destroyer can go 520ft at 70 mph
        #"CD0": 0.042,  # drag at 0 AoA  (based on disc speed)  2 deg AoA at 58mph was about 21m/s^2 with wobble, but only 5 after wobble subsides
        # (.055 at speed 11, .061 speed 5, .067 speed 4, .083 speed 2)
        "PDa": 1.67,  # quadratic with AoA from zero lift point (constant)
        "PTxwz": 0,  # rolling moment related to spin precession?
        "PTy0": -0.015, # pitching moment from disc stability at 0 AoA (based on turn of disc, also based on cavity of disc)
        # -0.02 turn -1, -0.007 turn 1, -0.033 turn -2, -0.015 turn 0  (per degree not per rad)
        "PTya": 0.3, # pitching moment from disc stability linear in AoA (0.006 / deg -> 0.343 / rad) (based on fade of disc)
        # fade 0 0.002, fade 1 0.004, fade 3  0.006, fade 5 0.008  (per degree not per rad)
        "PTxwx": -6.0e-4,  # dampening factor for wobble (constant) 21.5 -> 3.3 over 1s
        "PTzwz": -2.1e-5,  # spin down (constant) at 58mph spindown is about 24m/s^2 (3.5% (118.5 -> 114.5) over .82s)
        "I_xx": 6.263E-04 * 165/175, # I_xx is much closer to 1/2 on the destroyer than the condor, height is 2.2 vs 1.4
        # frequency of wobble for destroyer is .98 the rate of rotation.
        # this means that I_xx is about 1.01 * I_zz / 2
        "I_zz": 1.231E-03 * 165/175,
        "mass": 0.165,
        "diameter": 0.211,
        "rim_depth": 0.012,
        "rim_width": 0.0229,
        "height": 0.014,
    })

    # -2 turn
    destroyer: Model = Model(**{
        "PL0": 0.16,  # lift factor at 0 AoA (depends on glide) 2 deg Aoa at 58 mph lift was about 8m/s^2   0.8g
        "PLa": 2.29,  # lift factor linear with AoA (0.04 deg -> 2.29 rad) (constant)
        "PD0": 0.035, # keep dropping drag until destroyer can go 520ft at 70 mph
        #"CD0": 0.042,  # drag at 0 AoA  (based on disc speed)  2 deg AoA at 58mph was about 21m/s^2 with wobble, but only 5 after wobble subsides
        # (.055 at speed 11, .061 speed 5, .067 speed 4, .083 speed 2)
        "PDa": 1.67,  # quadratic with AoA from zero lift point (constant)
        "PTxwz": 0,  # rolling moment related to spin precession?
        "PTy0": -0.01, # pitching moment from disc stability at 0 AoA (based on turn of disc, also based on cavity of disc)
        # -0.02 turn -1, -0.007 turn 1, -0.033 turn -2, -0.015 turn 0  (per degree not per rad)
        "PTya": 0.3, # pitching moment from disc stability linear in AoA (0.006 / deg -> 0.343 / rad) (based on fade of disc)
        # fade 0 0.002, fade 1 0.004, fade 3  0.006, fade 5 0.008  (per degree not per rad)
        "PTxwx": -6.0e-4,  # dampening factor for wobble (constant) 21.5 -> 3.3 over 1s
        "PTzwz": -2.1e-5,  # spin down (constant) at 58mph spindown is about 24m/s^2 (3.5% (118.5 -> 114.5) over .82s)
        "I_xx": 6.263E-04, # I_xx is much closer to 1/2 on the destroyer than the condor, height is 2.2 vs 1.4
        # frequency of wobble for destroyer is .98 the rate of rotation.
        # this means that I_xx is about 1.01 * I_zz / 2
        "I_zz": 1.231E-03,
        "mass": 0.175,
        "diameter": 0.211,
        "rim_depth": 0.012,
        "rim_width": 0.0229,
        "height": 0.014,
    })

    # -0.68 turn
    stable_destroyer: Model = Model(**{
        "PL0": 0.16,  # lift factor at 0 AoA (depends on glide) 2 deg Aoa at 58 mph lift was about 8m/s^2   0.8g
        "PLa": 2.29,  # lift factor linear with AoA (0.04 deg -> 2.29 rad) (constant)
        "PD0": 0.035, # keep dropping drag until destroyer can go 520ft at 70 mph
        #"CD0": 0.042,  # drag at 0 AoA  (based on disc speed)  2 deg AoA at 58mph was about 21m/s^2 with wobble, but only 5 after wobble subsides
        # (.055 at speed 11, .061 speed 5, .067 speed 4, .083 speed 2)
        "PDa": 1.67,  # quadratic with AoA from zero lift point (constant)
        "PTxwz": 0,  # rolling moment related to spin precession?
        "PTy0": -0.0034, # pitching moment from disc stability at 0 AoA (based on turn of disc, also based on cavity of disc)
        # -0.02 turn -1, -0.007 turn 1, -0.033 turn -2, -0.015 turn 0  (per degree not per rad)
        "PTya": 0.3, # pitching moment from disc stability linear in AoA (0.006 / deg -> 0.343 / rad) (based on fade of disc)
        # fade 0 0.002, fade 1 0.004, fade 3  0.006, fade 5 0.008  (per degree not per rad)
        "PTxwx": -6.0e-4,  # dampening factor for wobble (constant) 21.5 -> 3.3 over 1s
        "PTzwz": -2.1e-5,  # spin down (constant) at 58mph spindown is about 24m/s^2 (3.5% (118.5 -> 114.5) over .82s)
        "I_xx": 6.263E-04, # I_xx is much closer to 1/2 on the destroyer than the condor, height is 2.2 vs 1.4
        # frequency of wobble for destroyer is .98 the rate of rotation.
        # this means that I_xx is about 1.01 * I_zz / 2
        "I_zz": 1.231E-03,
        "mass": 0.175,
        "diameter": 0.211,
        "rim_depth": 0.012,
        "rim_width": 0.0229,
        "height": 0.014,
    })

    # beefy has less turn and more fade
    # 0 turn
    beefy_destroyer: Model = Model(**{
        "PL0": 0.16,  # lift factor at 0 AoA (depends on glide) 2 deg Aoa at 58 mph lift was about 8m/s^2   0.8g
        "PLa": 2.29,  # lift factor linear with AoA (0.04 deg -> 2.29 rad) (constant)
        "PD0": 0.035, # keep dropping drag until destroyer can go 520ft at 70 mph
        #"CD0": 0.042,  # drag at 0 AoA  (based on disc speed)  2 deg AoA at 58mph was about 21m/s^2 with wobble, but only 5 after wobble subsides
        # (.055 at speed 11, .061 speed 5, .067 speed 4, .083 speed 2)
        "PDa": 1.67,  # quadratic with AoA from zero lift point (constant)
        "PTxwz": 0,  # rolling moment related to spin precession?
        "PTy0": 0, # pitching moment from disc stability at 0 AoA (based on turn of disc, also based on cavity of disc)
        # -0.02 turn -1, -0.007 turn 1, -0.033 turn -2, -0.015 turn 0  (per degree not per rad)
        "PTya": 0.3, # pitching moment from disc stability linear in AoA (0.006 / deg -> 0.343 / rad) (based on fade of disc)
        # fade 0 0.002, fade 1 0.004, fade 3  0.006, fade 5 0.008  (per degree not per rad)
        "PTxwx": -6.0e-4,  # dampening factor for wobble (constant) 21.5 -> 3.3 over 1s
        "PTzwz": -2.1e-5,  # spin down (constant) at 58mph spindown is about 24m/s^2 (3.5% (118.5 -> 114.5) over .82s)
        "I_xx": 6.263E-04, # I_xx is much closer to 1/2 on the destroyer than the condor, height is 2.2 vs 1.4
        # frequency of wobble for destroyer is .98 the rate of rotation.
        # this means that I_xx is about 1.01 * I_zz / 2
        "I_zz": 1.231E-03,
        "mass": 0.175,
        "diameter": 0.211,
        "rim_depth": 0.012,
        "rim_width": 0.0229,
        "height": 0.014,
    })

    xcal: Model = Model(**{
        "PL0": 0.16,  # lift factor at 0 AoA (depends on glide) 2 deg Aoa at 58 mph lift was about 8m/s^2   0.8g
        "PLa": 2.29,  # lift factor linear with AoA (0.04 deg -> 2.29 rad) (constant)
        "PD0": 0.035, # keep dropping drag until destroyer can go 520ft at 70 mph
        #"CD0": 0.042,  # drag at 0 AoA  (based on disc speed)  2 deg AoA at 58mph was about 21m/s^2 with wobble, but only 5 after wobble subsides
        # (.055 at speed 11, .061 speed 5, .067 speed 4, .083 speed 2)
        "PDa": 1.67,  # quadratic with AoA from zero lift point (constant)
        "PTxwz": 0,  # rolling moment related to spin precession?
        "PTy0": 0.002, # pitching moment from disc stability at 0 AoA (based on turn of disc, also based on cavity of disc)
        # -0.02 turn -1, -0.007 turn 1, -0.033 turn -2, -0.015 turn 0  (per degree not per rad)
        "PTya": 0.35, # pitching moment from disc stability linear in AoA (0.006 / deg -> 0.343 / rad) (based on fade of disc)
        # fade 0 0.002, fade 1 0.004, fade 3  0.006, fade 5 0.008  (per degree not per rad)
        "PTxwx": -6.0e-4,  # dampening factor for wobble (constant) 21.5 -> 3.3 over 1s
        "PTzwz": -2.1e-5,  # spin down (constant) at 58mph spindown is about 24m/s^2 (3.5% (118.5 -> 114.5) over .82s)
        "I_xx": 6.263E-04, # I_xx is much closer to 1/2 on the destroyer than the condor, height is 2.2 vs 1.4
        # frequency of wobble for destroyer is .98 the rate of rotation.
        # this means that I_xx is about 1.01 * I_zz / 2
        "I_zz": 1.231E-03,
        "mass": 0.175,
        "diameter": 0.211,
        "rim_depth": 0.012,
        "rim_width": 0.0229,
        "height": 0.014,
    })

    roc: Model = Model(**{
        "PL0": 0.053,  # lift factor at 0 AoA (depends on glide)
        # roc 0.053 glide 4, buzzz .1 glide 4, wraith .143 glide 5, aviar .152 glide 3, flick
        "PLa": 2.35,  # lift factor linear with AoA (0.04 deg -> 2.29 rad) (mostly constant, maybe dependent on glide)
        "CD0": 0.067,  # drag at 0 angle of attack  (based on disc speed)
        # (.055 at speed 11, .061 speed 5, .067 speed 4, .083 speed 2)
        "PDa": 1.67,  # quadratic with AoA from zero lift point (constant)
        "PTxwz": 0,  # rolling moment related to spin precession?
        "PTy0": -0.01,  # pitching from disc stability at 0 AoA (based on turn of disc, also based on cavity of disc)
        # -0.02 turn -1, -0.007 turn 1, -0.033 turn -2, -0.015 turn 0  (per degree not per rad)
        "PTya": 0.172,
        # pitching moment from disc stability linear in AoA (0.008 / deg -> 0.172) (based on fade of disc)
        # fade 0 0.002, fade 1 0.004, fade 3  0.006, fade 5 0.008  (per degree not per rad)
        "I_xx": 7.086E-04,
        "I_zz": 1.408E-03,
        "mass": 0.180,
        "diameter": 0.217,
        "rim_depth": 0.013,
        "rim_width": 0.012,
        "height": 0.020,
    })

    flick: Model = Model(**{
        "PL0": 0.05,  # lift factor at 0 AoA (depends on glide)
        # roc 0.053 glide 4, buzzz .1 glide 4, wraith .143 glide 5, aviar .152 glide 3, flick
        "PLa": 2.18,  # lift factor linear with AoA (0.038 deg -> 2.18 rad) (mostly constant, maybe dependent on glide)
        "PD0": 0.04,  # drag at 0 lift
        # (.055 at speed 11, .061 speed 5, .067 speed 4, .083 speed 2)
        "PDa": 1.67,  # quadratic with AoA from zero lift point (constant)
        "PTxwz": 0,  # rolling moment related to spin precession?
        "PTy0": -0.0017,  # pitching from disc stability at 0 AoA (based on turn of disc, also based on cavity of disc)
        # -0.02 turn -1, -0.007 turn 1, -0.033 turn -2, -0.015 turn 0  (per degree not per rad)
        "PTya": 0.458,
        # pitching moment from disc stability linear in AoA (0.008 / deg -> 0.172) (based on fade of disc)
        # fade 0 0.002, fade 1 0.004, fade 3  0.006, fade 5 0.008  (per degree not per rad)
        "I_xx": 6.183E-04,
        "I_zz": 1.231E-03,
        "mass": 0.175,
        "diameter": 0.211,
        "rim_depth": 0.012,
        "rim_width": 0.023,
        "height": 0.013,
    })
