# CPU racers. They read the course the same way a careful player would.
import random

from .input import blank
from .physics import Pilot, ghost_steer

# skill: jump timing. delay: frames a decision is held back. power: chance to
# go for a pickup. slow_hunt: chance to chase a slow bubble when behind.
DIFF = {
    "helppo": dict(skill=0.78, delay=3, power=0.35, slow_hunt=0.25, mistake=0.05),
    "normaali": dict(skill=0.92, delay=1, power=0.75, slow_hunt=0.8, mistake=0.015),
    "vaikea": dict(skill=1.0, delay=0, power=0.95, slow_hunt=1.0, mistake=0.0),
}


class CpuBrain:
    def __init__(self, difficulty, rng=None):
        self.spec = DIFF.get(difficulty, DIFF["normaali"])
        self.rng = rng or random.Random()
        self.pilot = Pilot(self.spec["skill"], self.rng)
        self.queue = []

    def decide(self, player, solids, hazards, powers, others):
        des = blank()
        if player.state == "ghost":
            ix, iy = ghost_steer(player.body, solids)
            des["x"] = ix
            des["y"] = iy
            return des
        if player.state != "run":
            return des
        _ix, held, pressed = self.pilot.decide(
            player.body, solids, hazards,
            glide=player.glide_t > 0,
            air_jumps=player.body.air_jumps,
        )
        # Reaction time delays the jump. It still happens, just late.
        self.queue.append((bool(held), bool(pressed)))
        lag = self.spec["delay"]
        if len(self.queue) <= lag:
            held, pressed = False, False
        else:
            held, pressed = self.queue.pop(0)
        if self.rng.random() < self.spec["mistake"]:
            held = False
            pressed = False
        des["x"] = 1.0
        des["jump"] = bool(held or pressed)
        return des
