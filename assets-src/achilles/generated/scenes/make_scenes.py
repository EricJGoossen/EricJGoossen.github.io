"""Generate Y-up contact scenes in the robot_on_plane.arow format: free-floating boxes over a ground slab."""
import math, sys, yaml
STATIC = [0]*36
FREE = [1 if r == c else 0 for r in range(6) for c in range(6)]

def world():
    return {"name": "world", "parent": None, "fields": dict(
        joint_subspace=STATIC, joint_activation_mask=[0],
        fixed_joint_transform={"translation": [0, 0, 0], "rotation": [1, 0, 0, 0]},
        rigid_body_inertia=[1, 0, 0, 0, 0.1, 0.1, 0.1, 0, 0, 0],
        joint_position={"translation": [0, 0, 0], "rotation": [1, 0, 0, 0]},
        joint_velocity=[0]*6, joint_torque=[0]*6, visual_extents=[0, 0, 0], visual_color=[0, 0, 0],
        collision_pose={"translation": [0, 0, 0], "rotation": [1, 0, 0, 0]},
        collision_extents=[0, 0, 0], collision_radius=[0], collision_margin=[0], collision_group=[0], collision_mask=[0])}

def ground(half=4):
    return {"name": "ground", "parent": "world", "fields": dict(
        joint_subspace=STATIC, joint_activation_mask=[0],
        fixed_joint_transform={"translation": [0, -0.2, 0], "rotation": [1, 0, 0, 0]},
        rigid_body_inertia=[1, 0, 0, 0, 0.1, 0.1, 0.1, 0, 0, 0],
        joint_position={"translation": [0, 0, 0], "rotation": [1, 0, 0, 0]},
        joint_velocity=[0]*6, joint_torque=[0]*6, visual_extents=[half, 0.1, half], visual_color=[0.35, 0.38, 0.35],
        collision_pose={"translation": [0, 0.1, 0], "rotation": [1, 0, 0, 0]},
        collision_extents=[half, 0.1, half], collision_radius=[0], collision_margin=[0.005],
        collision_group=[1], collision_mask=[2])}

def box(name, half, pos, quat=(1, 0, 0, 0), vel=(0, 0, 0, 0, 0, 0), mass=1.0, color=(0.62, 0.66, 0.72), r=0.005):
    """A free box whose frame sits at its bottom-center (the viewer draws boxes from the frame up local +y)."""
    a, b, c = half
    Ixx = mass * (b*b + c*c) / 3 + mass * b * b
    Iyy = mass * (a*a + c*c) / 3
    Izz = mass * (a*a + b*b) / 3 + mass * b * b
    return {"name": name, "parent": "world", "fields": dict(
        joint_subspace=FREE, joint_activation_mask=[63],
        fixed_joint_transform={"translation": [0, 0, 0], "rotation": [1, 0, 0, 0]},
        rigid_body_inertia=[mass, 0, mass * b, 0, Ixx, Iyy, Izz, 0, 0, 0],
        joint_position={"translation": list(pos), "rotation": list(quat)},
        joint_velocity=list(vel), joint_torque=[0]*6,
        visual_extents=list(half), visual_color=list(color),
        collision_pose={"translation": [0, b, 0], "rotation": [1, 0, 0, 0]},
        collision_extents=[a - r, b - r, c - r], collision_radius=[r], collision_margin=[0.005],
        collision_group=[2], collision_mask=[3])}

PAL = [(0.16, 0.47, 0.84), (0.92, 0.41, 0.20), (0.11, 0.69, 0.48), (0.93, 0.63, 0.0), (0.91, 0.48, 0.64), (0.38, 0.31, 0.84)]

def dominoes(n=12, gap=0.22):
    half = (0.025, 0.25, 0.1)
    js = [world(), ground()]
    for i in range(n):
        vel = (0, 0, -2.2, 0, 0, 0) if i == 0 else (0, 0, 0, 0, 0, 0)
        js.append(box(f"d{i}", half, ((i - (n - 1) / 2) * gap, 0.0005, 0), vel=vel, mass=0.3, color=PAL[i % len(PAL)]))
    return {"archetype": "dominoes", "joints": js}

def tower(n=8, size=0.12):
    js = [world(), ground()]
    for i in range(n):
        js.append(box(f"b{i}", (size, size * 0.5, size), (0, i * size + 0.0005, 0), mass=1.0, color=PAL[i % len(PAL)]))
    return {"archetype": "tower", "joints": js}

out = sys.argv[1]
for name, doc in (("dominoes", dominoes()), ("tower", tower())):
    open(f"{out}/{name}.arow", "w").write(yaml.safe_dump(doc, sort_keys=False, default_flow_style=None))
open(f"{out}/sim_config.yaml", "w").write("base_acceleration:\n  angular: [0, 0, 0]\n  linear: [0, 9.81, 0]\n")

def dominoes_view(n=14, gap=0.42, half=(0.04, 0.42, 0.18), yaw=0.7, push=-1.6, grow=1.0):
    """Dominoes laid across the viewer's default camera (yaw 0.7 rad): the line runs at
    phi = pi/2 - yaw about +y, so it crosses the view side-on. Optionally each one `grow`x bigger."""
    phi = math.pi / 2 - yaw
    q = (math.cos(phi / 2), 0, math.sin(phi / 2), 0)
    dx, dz = math.cos(phi), -math.sin(phi)
    js = [world(), ground(6)]
    s, pos = 1.0, -(n - 1) / 2 * gap
    for i in range(n):
        h = tuple(v * s for v in half)
        vel = (0, 0, push, 0, 0, 0) if i == 0 else (0, 0, 0, 0, 0, 0)
        js.append(box(f"d{i}", h, (pos * dx, 0.0005, pos * dz), quat=q, vel=vel, mass=0.5 * s**3, color=PAL[i % len(PAL)]))
        pos += gap * s * (1 + grow) / 2 if grow != 1.0 else gap
        s *= grow
    return {"archetype": "dominoes", "joints": js}

if __name__ == "__main__" and len(sys.argv) > 2:
    doc = dominoes_view() if sys.argv[2] == "dv" else None
    open(f"{sys.argv[1]}/{sys.argv[3]}.arow", "w").write(yaml.safe_dump(doc, sort_keys=False, default_flow_style=None))
