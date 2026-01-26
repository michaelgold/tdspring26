"""Week 2 Exercise 3: CLI pipeline driver with presets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy

SAVE_NAME = "week2ex3.blend"
RENDER_PREFIX = "week2_ex3_"


def parse_args() -> argparse.Namespace:
    argv: list[str] = []
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1 :]
    parser = argparse.ArgumentParser(description="Week 2 pipeline driver")
    parser.add_argument(
        "--preset", choices=("turntable", "closeup"), default="turntable"
    )
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).parent / "renders"
    )
    parser.add_argument(
        "--render", action="store_true", help="Render after scene build"
    )
    return parser.parse_args(argv)


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


def add_base_environment() -> None:
    bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0.0, 0.0, 0.0))
    plane = bpy.context.active_object
    plane.name = "PipelineFloor"
    mat = bpy.data.materials.new(name="PipelineFloorMaterial")  # type: ignore
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs[0].default_value = (0.04, 0.04, 0.05, 1.0)
    bsdf.inputs[7].default_value = 0.6
    plane.data.materials.append(mat)


def add_hero_object() -> bpy.types.Object:
    bpy.ops.mesh.primitive_monkey_add(size=1.5)
    hero = bpy.context.active_object
    hero.name = "PipelineHero"
    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.new(name="PipelineHeroMaterial")  # type: ignore
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs[0].default_value = (0.2, 0.6, 0.9, 1.0)
    bsdf.inputs[5].default_value = 0.9
    hero.data.materials.append(mat)
    return hero


def point(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    from mathutils import Vector
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def create_camera(
    name: str, location: tuple[float, float, float], target: tuple[float, float, float], lens: float = 50.0
) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new(name=name)  # type: ignore
    camera_obj = bpy.data.objects.new(name, camera_data)  # type: ignore
    bpy.context.collection.objects.link(camera_obj)  # type: ignore
    camera_obj.location = location
    camera_data.lens = lens
    point(camera_obj, target)
    bpy.context.scene.camera = camera_obj
    return camera_obj


def create_light_rig() -> None:
    sun_data = bpy.data.lights.new(name="PipelineKey", type="SUN")  # type: ignore
    sun = bpy.data.objects.new("PipelineKey", sun_data)  # type: ignore
    bpy.context.collection.objects.link(sun)  # type: ignore
    sun.location = (10.0, -6.0, 14.0)
    point(sun, (0.0, 0.0, 1.0))
    sun_data.energy = 4.5

    rim_data = bpy.data.lights.new(name="PipelineRim", type="AREA")  # type: ignore
    rim = bpy.data.objects.new("PipelineRim", rim_data)  # type: ignore
    bpy.context.collection.objects.link(rim)  # type: ignore
    rim.location = (-8.0, 4.0, 6.0)
    rim.rotation_euler = (0.0, 0.0, 1.2)
    rim_data.energy = 900.0
    rim_data.shape = "RECTANGLE"
    rim_data.size = 6.0
    rim_data.size_y = 2.0


def build_turntable_scene() -> None:
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 120
    hero = add_hero_object()
    hero.animation_data_clear()
    keyframes = (
        (1, 0.0),
        (60, 3.14159),
        (120, 6.28318),
    )
    for frame, rotation in keyframes:
        hero.rotation_euler = (0.0, 0.0, rotation)
        hero.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)
    create_camera(
        "TurntableCam", (8.0, -8.0, 5.0), (0.0, 0.0, 1.0), lens=45.0
    )


def build_closeup_scene() -> None:
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 48
    hero = add_hero_object()
    hero.location = (0.0, 0.0, 0.5)
    camera = create_camera(
        "CloseupCam", (1.5, -1.0, 1.5), (0.0, 0.0, 0.8), lens=75.0
    )
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 1.5


def render_output(output_dir: Path, preset: str, animation: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{RENDER_PREFIX}{preset}"
    bpy.context.scene.render.filepath = str(filepath)
    if animation:
        bpy.ops.render.render(animation=True)
    else:
        bpy.context.scene.frame_set(1)
        bpy.ops.render.render(write_still=True)


def main() -> None:
    args = parse_args()
    reset_scene()
    clear_objects()
    add_base_environment()
    create_light_rig()

    builders = {
        "turntable": (build_turntable_scene, True),
        "closeup": (build_closeup_scene, False),
    }

    build_fn, renders_animation = builders[args.preset]
    build_fn()

    if args.render:
        render_output(args.output, args.preset, renders_animation)

    save_path = Path(__file__).with_name(SAVE_NAME)
    bpy.ops.wm.save_as_mainfile(filepath=str(save_path))
    print(f"Week 2 Exercise 3 saved to {save_path}")


if __name__ == "__main__":
    main()
