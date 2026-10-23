"""The handover scene: the OpenArm model plus a table, a can (a mocap body the
scripts move to follow the gripper holding it) and, for rendering, a floor."""


def scene_xml(src, table_z, can_half, floor=False):
    """src is the generated OpenArm bimanual model's XML."""
    leg = (table_z - 0.03) / 2
    legs = "".join(
        f'<geom name="table_leg{i}" type="box" size="0.015 0.015 {leg}" pos="{x} {y} {leg}" rgba="0.25 0.26 0.28 1"/>'
        for i, (x, y) in enumerate([(0.14, 0.27), (0.14, -0.27), (-0.14, 0.27), (-0.14, -0.27)])
    )
    bodies = f"""
    <body name="table" pos="0.45 0 0">
      <geom name="table_top" type="box" size="0.17 0.30 0.015" pos="0 0 {table_z - 0.015}" rgba="0.36 0.37 0.40 1"/>
      {legs}
    </body>
    <body name="can_prop" mocap="true" pos="0 0 -1">
      <geom name="can_prop_visual" type="cylinder" size="0.033 {can_half}" rgba="0.85 0.12 0.12 1" contype="0" conaffinity="0" group="2"/>
      <geom name="can_prop_lid" type="cylinder" size="0.031 0.002" pos="0 0 {can_half}" rgba="0.8 0.8 0.82 1" contype="0" conaffinity="0" group="2"/>
    </body>
"""
    if floor:
        bodies += '<geom name="floor" type="plane" size="0 0 0.05" material="grid_floor" contype="0" conaffinity="0" group="2"/>'
        src = src.replace(
            "<asset>",
            '<asset><texture name="grid_tex" type="2d" builtin="checker" rgb1="0.06 0.067 0.078" rgb2="0.06 0.067 0.078" '
            'mark="edge" markrgb="0.32 0.33 0.36" width="256" height="256"/>'
            '<material name="grid_floor" texture="grid_tex" texrepeat="8 8" texuniform="true" reflectance="0"/>',
            1,
        )
    return src.replace('<site name="world_site"/>', '<site name="world_site"/>' + bodies, 1)
