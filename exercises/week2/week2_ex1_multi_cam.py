"""Week 2 Exercise 1: multi-camera and lighting preset automation."""

import math
from pathlib import Path

import bpy

SAVE_NAME = "week2ex1.blend"
OUTPUT_PREFIX = "week2_ex1_"

CAMERA_PRESETS = (
    {
        "name": "wide",
        "location": (8.0, -6.0, 5.0),
        "target": (0.0, 0.0, 1.2),
        "lens": 35.0,
        "light_mode": "studio",
    },
    {
        "name": "profile",
        "location": (-6.0, -2.0, 3.5),
        "target": (0.0, 0.0, 1.0),
        "lens": 70.0,
        "light_mode": "rim",
    },
    {
        "name": "topdown",
        "location": (0.0, -1.0, 9.0),
        "target": (0.0, 0.0, 0.0),
        "lens": 28.0,
        "light_mode": "studio",
    },
)

LIGHT_MODES = {
    "studio": {
        "key_energy": 4.0,
        "fill_energy": 900.0,
        "fill_color": (0.9, 0.95, 1.0, 1.0),
    },
    "rim": {
        "key_energy": 6.0,
        "fill_energy": 500.0,
        "fill_color": (1.0, 0.7, 0.4, 1.0),
    },
}


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.image_settings.file_format = "PNG"


def ensure_object_mode() -> None:
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def clear_objects() -> None:
    ensure_object_mode()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def add_floor() -> None:
    bpy.ops.mesh.primitive_plane_add(size=30.0, location=(0.0, 0.0, -1.0))
    plane = bpy.context.active_object
    mat = bpy.data.materials.new(name="Week2Floor")  # type: ignore[attr-defined]
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs[0].default_value = (0.05, 0.05, 0.06, 1.0)
    plane.data.materials.append(mat)


def add_hero() -> bpy.types.Object:
    bpy.ops.mesh.primitive_monkey_add(size=1.4)
    hero = bpy.context.active_object
    hero.name = "Week2Hero"
    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.new(name="Week2HeroMaterial")  # type: ignore[attr-defined]
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs[0].default_value = (0.45, 0.7, 1.0, 1.0)
    bsdf.inputs[5].default_value = 0.75
    hero.data.materials.append(mat)
    return hero


def create_camera() -> bpy.types.Object:
    camera_data = bpy.data.cameras.new(name="PresetCamera")  # type: ignore[attr-defined]
    camera_obj = bpy.data.objects.new("PresetCamera", camera_data)  # type: ignore[attr-defined]
    bpy.context.collection.objects.link(camera_obj)  # type: ignore[attr-defined]
    bpy.context.scene.camera = camera_obj
    return camera_obj


def create_lights() -> tuple[bpy.types.Object, bpy.types.Object]:
    key_data = bpy.data.lights.new(name="PresetKey", type="SUN")  # type: ignore[attr-defined]
    key = bpy.data.objects.new("PresetKey", key_data)  # type: ignore[attr-defined]
    bpy.context.collection.objects.link(key)  # type: ignore[attr-defined]
    key.location = (12.0, -8.0, 16.0)

    fill_data = bpy.data.lights.new(name="PresetFill", type="AREA")  # type: ignore[attr-defined]
    fill = bpy.data.objects.new("PresetFill", fill_data)  # type: ignore[attr-defined]
    bpy.context.collection.objects.link(fill)  # type: ignore[attr-defined]
    fill.location = (-6.0, 4.0, 5.0)
    fill.rotation_euler = (0.0, 0.0, 0.4)
    fill_data.shape = "RECTANGLE"
    fill_data.size = 6.0
    fill_data.size_y = 3.0
    return key, fill


def point(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    ox, oy, oz = obj.location
    tx, ty, tz = target
    dx, dy, dz = tx - ox, ty - oy, tz - oz
    distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    if distance == 0.0:
        return
    fx, fy, fz = -(dx / distance), -(dy / distance), -(dz / distance)
    yaw = math.atan2(fx, fy)
    pitch = math.atan2(fz, math.hypot(fx, fy))
    obj.rotation_euler = (pitch, 0.0, yaw)


def apply_light_mode(key: bpy.types.Object, fill: bpy.types.Object, mode: str) -> None:
    config = LIGHT_MODES[mode]
    key.data.energy = config["key_energy"]
    fill.data.energy = config["fill_energy"]
    fill.data.color = config["fill_color"]


def render_shot(output_path: Path) -> None:
    bpy.context.scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    reset_scene()
    clear_objects()
    add_floor()
    hero = add_hero()
    camera = create_camera()
    key_light, fill_light = create_lights()
    output_dir = Path(__file__).parent

    for preset in CAMERA_PRESETS:
        camera.location = preset["location"]
        camera.data.lens = preset["lens"]
        target = preset["target"]
        point(camera, target)
        point(key_light, target)
        apply_light_mode(key_light, fill_light, preset["light_mode"])
        filepath = output_dir / f"{OUTPUT_PREFIX}{preset['name']}.png"
        render_shot(filepath)
        print(f"Rendered {filepath.name}")

    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / SAVE_NAME))
    print("Week 2 Exercise 1 complete")


if __name__ == "__main__":
    main()
