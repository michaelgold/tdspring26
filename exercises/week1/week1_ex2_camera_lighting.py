"""Week 1 Exercise 2: build a procedural camera + lighting rig and render a still."""

import math
from pathlib import Path

import bpy

SAVE_NAME = "week1ex2.blend"
STILL_NAME = "week1ex2.png"


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


def add_floor() -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=25.0, location=(0.0, 0.0, -1.5))
    plane = bpy.context.active_object
    mat = bpy.data.materials.new(name="Floor")  # type: ignore[attr-defined]
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs[0].default_value = (0.07, 0.07, 0.07, 1.0)
    bsdf.inputs[7].default_value = 0.8  # roughness
    plane.data.materials.append(mat)
    return plane


def add_hero_object() -> bpy.types.Object:
    bpy.ops.mesh.primitive_monkey_add(size=1.5, location=(0.0, 0.0, 0.0))
    obj = bpy.context.active_object
    obj.name = "HeroSuzanne"
    mat = bpy.data.materials.new(name="Hero")  # type: ignore[attr-defined]
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs[0].default_value = (0.85, 0.5, 0.1, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.4
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return obj


def aim_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    ox, oy, oz = obj.location
    tx, ty, tz = target
    dx, dy, dz = tx - ox, ty - oy, tz - oz
    distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    if distance == 0.0:
        return

    # Local -Z should point toward the target; flip the forward vector to derive pitch/yaw.
    fx, fy, fz = -(dx / distance), -(dy / distance), -(dz / distance)
    yaw = math.atan2(fx, fy)
    pitch = math.atan2(fz, math.hypot(fx, fy))
    obj.rotation_euler = (pitch, 0.0, yaw)


def add_camera(target: tuple[float, float, float]) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new(name="TD_Camera")  # type: ignore[attr-defined]
    camera_object = bpy.data.objects.new("TD_Camera", camera_data)  # type: ignore[attr-defined]
    bpy.context.collection.objects.link(camera_object)  # type: ignore[attr-defined]
    camera_object.location = (8.0, -8.0, 6.0)
    aim_at(camera_object, target)
    bpy.context.scene.camera = camera_object
    return camera_object


def add_lights(target: tuple[float, float, float]) -> None:
    sun_data = bpy.data.lights.new(name="KeySun", type="SUN")  # type: ignore[attr-defined]
    sun = bpy.data.objects.new("KeySun", sun_data)  # type: ignore[attr-defined]
    bpy.context.collection.objects.link(sun)  # type: ignore[attr-defined]
    sun.location = (12.0, -6.0, 15.0)
    aim_at(sun, target)
    sun_data.energy = 2.5

    fill_data = bpy.data.lights.new(name="FillLight", type="AREA")  # type: ignore[attr-defined]
    fill = bpy.data.objects.new("FillLight", fill_data)  # type: ignore[attr-defined]
    bpy.context.collection.objects.link(fill)  # type: ignore[attr-defined]
    fill.location = (-6.0, 4.0, 5.0)
    fill.rotation_euler = (0.0, 0.0, 0.6)
    fill_data.energy = 600.0
    fill_data.shape = "RECTANGLE"
    fill_data.size = 4.0
    fill_data.size_y = 2.0


def render_still(output_path: Path) -> None:
    bpy.context.scene.frame_set(1)
    bpy.context.scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    reset_scene()
    clear_objects()
    add_floor()
    hero = add_hero_object()
    hero_location = tuple(hero.location)
    add_camera(hero_location)
    add_lights(hero_location)
    render_still(Path(__file__).with_name(STILL_NAME))
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name(SAVE_NAME)))
    print("Week 1 Exercise 2 complete")


if __name__ == "__main__":
    main()
