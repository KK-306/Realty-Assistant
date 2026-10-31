"""Manual low-resource render check: four bundled photos, 15 seconds, 720p/24 FPS."""

import json
import tempfile
import uuid
from pathlib import Path

from app.config import OUTPUT_DIR, SAMPLE_DIR, settings
from app.models.property import AspectRatio, PropertyInput, VisualTheme
from app.models.storyboard import SceneOverlay, ScriptOutput, StoryboardOutput, StoryboardScene
from app.services.video_renderer import VideoRenderer

SMOKE_IMAGE_IDS = [
    "1_exterior_facade.jpg",
    "2_living_room.jpg",
    "3_modular_kitchen.jpg",
    "4_master_bedroom.jpg",
]
SMOKE_DURATION_SECONDS = 15


def make_smoke_storyboard() -> tuple[PropertyInput, StoryboardOutput]:
    prop = PropertyInput.model_construct(
        property_name="Render Smoke Test",
        location="Mohali, Punjab",
        price=8500000,
        price_display="₹85 Lakh",
        key_features=["Living room", "Modular kitchen", "Master bedroom"],
        bedrooms=2,
        bathrooms=2,
        cta_text="Schedule a Visit",
        duration=SMOKE_DURATION_SECONDS,
        aspect_ratio=AspectRatio.LANDSCAPE,
        theme=VisualTheme.MODERN,
        narration_enabled=False,
        music_enabled=True,
        image_ids=SMOKE_IMAGE_IDS,
    )
    scenes = []
    for index, image_id in enumerate(SMOKE_IMAGE_IDS):
        title = ["Greenview Residency", "Open Living Space", "Modular Kitchen", "Schedule a Visit"][index]
        scenes.append(
            StoryboardScene(
                scene_index=index,
                scene_type=["opening", "feature", "feature", "closing"][index],
                duration=SMOKE_DURATION_SECONDS / len(SMOKE_IMAGE_IDS),
                image_id=image_id,
                image_index=index,
                caption=title,
                voiceover_text="",
                overlay=SceneOverlay(
                    tag="RENDER SMOKE TEST",
                    title=title,
                    subtitle="Four-image low-resource rendering check",
                    badge="₹85 Lakh",
                    footer="Mohali, Punjab",
                ),
            )
        )

    storyboard = StoryboardOutput(
        script=ScriptOutput(
            video_title="Render Smoke Test",
            opening_hook="",
            voiceover_full="",
            closing_cta="Schedule a Visit",
            scene_voiceovers=[],
        ),
        scenes=scenes,
        total_duration=float(SMOKE_DURATION_SECONDS),
        aspect_ratio=AspectRatio.LANDSCAPE.value,
        theme=VisualTheme.MODERN.value,
    )
    return prop, storyboard


def main() -> None:
    missing_images = [image_id for image_id in SMOKE_IMAGE_IDS if not (SAMPLE_DIR / image_id).is_file()]
    if missing_images:
        raise FileNotFoundError(f"Bundled smoke-test images are missing: {', '.join(missing_images)}")

    prop, storyboard = make_smoke_storyboard()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="render-smoke-", dir=OUTPUT_DIR) as result_dir:
        output_mp4 = Path(result_dir) / f"smoke-{uuid.uuid4().hex}.mp4"
        metadata = VideoRenderer.render_video(storyboard, prop, output_mp4)
        if not output_mp4.is_file() or metadata["file_size_bytes"] < 1000:
            raise RuntimeError("Smoke render returned without a usable MP4 file.")
        if metadata["duration_seconds"] != SMOKE_DURATION_SECONDS:
            raise RuntimeError(f"Expected a 15-second render, received {metadata['duration_seconds']} seconds.")
        if (metadata["width"], metadata["height"], metadata["fps"]) != (1280, 720, 24):
            raise RuntimeError(f"Unexpected smoke render settings: {metadata}")
        print(json.dumps({"result": "passed", "ffmpeg": settings.get_ffmpeg_path(), **metadata}, indent=2))


if __name__ == "__main__":
    main()
