"""Week 1 Exercise 3: placeholder character import + automated render pipeline."""

import math
from pathlib import Path

import bpy

SAVE_NAME = "week1ex3.blend"
RENDER_PREFIX = "week1ex3_"
CHARACTER_FBX = Path(__file__).with_name("placeholder_character.fbx")
FRAME_START = 1
FRAME_END = 90
STEP = 10
Y_OFFSET = -3.0
Z_OFFSET = 3.0


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.frame_start = FRAME_START
    bpy.context.scene.frame_end = FRAME_END


def ensure_object_mode() -> None:
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def clear_objects() -> None:
    ensure_object_mode()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def build_environment() -> None:
    bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0.0, 0.0, -1.0))
    plane = bpy.context.active_object
    mat = bpy.data.materials.new(name="EnvFloor")  # type: ignore[attr-defined]
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs[0].default_value = (0.02, 0.02, 0.025, 1.0)
    plane.data.materials.append(mat)


def import_character(asset_path: Path) -> bpy.types.Object:
    ensure_object_mode()
    if asset_path.exists():
        bpy.ops.import_scene.fbx(filepath=str(asset_path))
        objects = list(bpy.context.selected_objects)
        character = objects[0] if objects else bpy.context.active_object
        print(f"Imported character from {asset_path}")
    else:
        bpy.ops.mesh.primitive_monkey_add(size=1.2, location=(0.0, 0.0, 0.0))
        character = bpy.context.active_object
        character.name = "ProxyCharacter"
        print("Placeholder character created (no FBX found).")
    bpy.ops.object.shade_smooth()
    return character


def animate_character(obj: bpy.types.Object) -> None:
    obj.animation_data_clear()
    beats = (
        (FRAME_START, (0.0, 0.0, 0.0)),
        (30, (0.5, 1.5, 0.0)),
        (60, (1.5, 3.0, 0.0)),
        (FRAME_END, (3.5, 4.5, 0.0)),
    )
    for frame, location in beats:
        obj.location = location
        obj.keyframe_insert(data_path="location", frame=frame)


def point_camera_to_target(
    cam: bpy.types.Object, target_loc: tuple[float, float, float]
) -> None:
    ox, oy, oz = cam.location
    tx, ty, tz = target_loc
    dx, dy, dz = tx - ox, ty - oy, tz - oz
    distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    if distance == 0.0:
        return
    fx, fy, fz = -(dx / distance), -(dy / distance), -(dz / distance)
    yaw = math.atan2(fx, fy)
    pitch = math.atan2(fz, math.hypot(fx, fy))
    cam.rotation_euler = (pitch, 0.0, yaw)


def setup_camera(target: bpy.types.Object) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new(name="FollowCamera")  # type: ignore[attr-defined]
    camera_object = bpy.data.objects.new("FollowCamera", camera_data)  # type: ignore[attr-defined]
    bpy.context.collection.objects.link(camera_object)  # type: ignore[attr-defined]
    target_y, target_z = target.location.y, target.location.z
    camera_object.location = (0.0, target_y + Y_OFFSET, target_z + Z_OFFSET)
    bpy.context.scene.camera = camera_object
    for frame in range(FRAME_START, FRAME_END + 1, STEP):
        bpy.context.scene.frame_set(frame)
        target_location = target.matrix_world.translation
        target_tuple = tuple(target_location)
        camera_object.location = (
            target_tuple[0],
            target_tuple[1] + Y_OFFSET,
            max(target_tuple[2] + Z_OFFSET, 0.5),
        )
        point_camera_to_target(camera_object, target_tuple)
        camera_object.keyframe_insert(data_path="location", frame=frame)
        camera_object.keyframe_insert(data_path="rotation_euler", frame=frame)
    return camera_object


def add_lights(target: bpy.types.Object) -> None:
    sun_data = bpy.data.lights.new(name="RigKey", type="SUN")  # type: ignore[attr-defined]
    sun = bpy.data.objects.new("RigKey", sun_data)  # type: ignore[attr-defined]
    bpy.context.collection.objects.link(sun)  # type: ignore[attr-defined]
    sun.location = (12.0, -12.0, 20.0)
    point_camera_to_target(sun, tuple(target.location))
    sun_data.energy = 4.0

    rim_data = bpy.data.lights.new(name="RigRim", type="AREA")  # type: ignore[attr-defined]
    rim = bpy.data.objects.new("RigRim", rim_data)  # type: ignore[attr-defined]
    bpy.context.collection.objects.link(rim)  # type: ignore[attr-defined]
    rim.location = (-8.0, 6.0, 5.0)
    rim.rotation_euler = (0.0, 0.0, 1.2)
    rim_data.energy = 1200.0
    rim_data.shape = "RECTANGLE"
    rim_data.size = 6.0
    rim_data.size_y = 1.0


def render_animation(output_prefix: Path) -> None:
    bpy.context.scene.frame_set(FRAME_START)
    bpy.context.scene.render.filepath = str(output_prefix)
    bpy.ops.render.render(animation=True)


def main() -> None:
    reset_scene()
    clear_objects()
    build_environment()
    character = import_character(CHARACTER_FBX)
    animate_character(character)
    add_lights(character)
    setup_camera(character)
    render_animation(Path(__file__).with_name(RENDER_PREFIX))
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name(SAVE_NAME)))
    print("Week 1 Exercise 3 complete — swap in your character FBX when ready.")


if __name__ == "__main__":
    main()
