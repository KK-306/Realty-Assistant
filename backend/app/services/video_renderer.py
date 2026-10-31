import os
import asyncio
import subprocess
import shutil
import logging
import re
import time
import uuid
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFont, ImageOps

from app.config import settings
from app.models.property import PropertyInput, VisualTheme
from app.models.storyboard import StoryboardOutput, StoryboardScene
from app.services.file_storage import FileStorageService
from app.services.audio_service import AudioService

logger = logging.getLogger(__name__)


class FFmpegExecutionError(RuntimeError):
    def __init__(self, message: str, *, returncode: Optional[int] = None, timed_out: bool = False):
        super().__init__(message)
        self.returncode = returncode
        self.timed_out = timed_out

class VideoRenderer:
    @staticmethod
    def _probe_audio_duration(audio_path: Path, ffmpeg_bin: str, timeout: int = 30) -> Optional[float]:
        """Reads media duration from FFmpeg so speech can be kept inside its scene."""
        try:
            result = VideoRenderer._run_ffmpeg(
                [
                    ffmpeg_bin, "-hide_banner", "-loglevel", "info", "-threads", "1",
                    "-i", str(audio_path), "-f", "null", "-",
                ],
                f"audio duration probe for {audio_path.name}",
                timeout=timeout,
            )
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
            if not match:
                return None
            hours, minutes, seconds = match.groups()
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        except Exception:
            logger.warning("Could not probe audio duration for %s; using scene duration", audio_path, exc_info=True)
            return None

    @staticmethod
    def _get_font(font_size: int, bold: bool = False, serif: bool = False) -> ImageFont.ImageFont:
        """
        Attempts to load a clean modern font with fallbacks.
        """
        candidates = []
        if serif:
            candidates.extend([
                r"C:\Windows\Fonts\georgia.ttf",
                r"C:\Windows\Fonts\times.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
            ])
        if bold:
            candidates.extend([
                r"C:\Windows\Fonts\segoeuib.ttf",
                r"C:\Windows\Fonts\arialbd.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            ])
        else:
            candidates.extend([
                r"C:\Windows\Fonts\segoeui.ttf",
                r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\calibri.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            ])

        for c in candidates:
            if os.path.isfile(c):
                try:
                    return ImageFont.truetype(c, font_size)
                except Exception:
                    continue

        return ImageFont.load_default()

    @classmethod
    def _create_scene_overlay(
        cls,
        scene: StoryboardScene,
        prop: PropertyInput,
        target_w: int,
        target_h: int,
        temp_dir: Optional[Path] = None,
    ) -> Path:
        """
        Renders a crystal-clear, high-contrast translucent graphics card with
        brand typography, tags, and badges for a given scene.
        """
        overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Visual Theme Color Palettes
        theme_palettes = {
            VisualTheme.LUXURY: {
                "bg_color": (10, 15, 26, 225),
                "border_color": (212, 175, 55, 240),      # Rich Gold
                "tag_bg": (212, 175, 55, 255),
                "tag_text": (10, 15, 26),
                "title_color": (255, 255, 255),
                "subtitle_color": (226, 232, 240),
                "badge_bg": (30, 41, 59, 230),
                "badge_text": (212, 175, 55),
                "footer_color": (148, 163, 184),
                "serif": True
            },
            VisualTheme.MODERN: {
                "bg_color": (15, 23, 42, 220),
                "border_color": (6, 182, 212, 240),       # Electric Cyan
                "tag_bg": (6, 182, 212, 255),
                "tag_text": (15, 23, 42),
                "title_color": (255, 255, 255),
                "subtitle_color": (203, 213, 225),
                "badge_bg": (30, 41, 59, 230),
                "badge_text": (6, 182, 212),
                "footer_color": (148, 163, 184),
                "serif": False
            },
            VisualTheme.MINIMAL: {
                "bg_color": (18, 18, 18, 225),
                "border_color": (245, 245, 245, 240),     # Clean Crisp White
                "tag_bg": (245, 245, 245, 255),
                "tag_text": (18, 18, 18),
                "title_color": (255, 255, 255),
                "subtitle_color": (212, 212, 216),
                "badge_bg": (38, 38, 38, 230),
                "badge_text": (255, 255, 255),
                "footer_color": (161, 161, 170),
                "serif": False
            },
            VisualTheme.ELEGANT: {
                "bg_color": (28, 20, 24, 225),
                "border_color": (224, 169, 150, 240),     # Rose Gold / Warm Bronze
                "tag_bg": (224, 169, 150, 255),
                "tag_text": (28, 20, 24),
                "title_color": (255, 255, 255),
                "subtitle_color": (241, 228, 224),
                "badge_bg": (45, 30, 36, 230),
                "badge_text": (224, 169, 150),
                "footer_color": (196, 175, 170),
                "serif": True
            }
        }
        pal = theme_palettes.get(prop.theme, theme_palettes[VisualTheme.LUXURY])

        # Dimensions based on aspect ratio
        is_vertical = (target_h > target_w)
        if is_vertical:
            # 9:16 layout
            card_w = int(target_w * 0.90)
            card_h = int(target_h * 0.28)
            card_x = (target_w - card_w) // 2
            card_y = target_h - card_h - int(target_h * 0.08)
            font_title_size = 46
            font_sub_size = 28
            font_tag_size = 20
        else:
            # 16:9 layout
            card_w = int(target_w * 0.65)
            card_h = int(target_h * 0.28)
            card_x = (target_w - card_w) // 2
            card_y = target_h - card_h - int(target_h * 0.07)
            font_title_size = 42
            font_sub_size = 26
            font_tag_size = 18

        # Draw card background with rounded rect and subtle border
        draw.rounded_rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            radius=18,
            fill=pal["bg_color"],
            outline=pal["border_color"],
            width=2
        )

        font_tag = cls._get_font(font_tag_size, bold=True)
        font_title = cls._get_font(font_title_size, bold=True, serif=pal["serif"])
        font_sub = cls._get_font(font_sub_size, bold=False)
        font_badge = cls._get_font(font_tag_size + 2, bold=True)

        ov_data = scene.overlay
        current_y = card_y + 24

        # 1. Tag / Badge
        tag_str = (ov_data.tag or "FEATURED").upper()
        tag_bbox = draw.textbbox((0, 0), tag_str, font=font_tag)
        tag_text_w = tag_bbox[2] - tag_bbox[0]
        tag_text_h = tag_bbox[3] - tag_bbox[1]
        
        tag_pad_x = 16
        tag_pad_y = 6
        tag_box_w = tag_text_w + (tag_pad_x * 2)
        tag_box_h = tag_text_h + (tag_pad_y * 2)
        tag_box_x = card_x + 36

        draw.rounded_rectangle(
            [tag_box_x, current_y, tag_box_x + tag_box_w, current_y + tag_box_h],
            radius=6,
            fill=pal["tag_bg"]
        )
        draw.text((tag_box_x + tag_pad_x, current_y + tag_pad_y - 2), tag_str, fill=pal["tag_text"], font=font_tag)

        # Price badge on opposite side if present
        if ov_data.badge:
            badge_str = ov_data.badge
            b_bbox = draw.textbbox((0, 0), badge_str, font=font_badge)
            b_w = b_bbox[2] - b_bbox[0]
            b_h = b_bbox[3] - b_bbox[1]
            b_box_w = b_w + 24
            b_box_h = b_h + 12
            b_box_x = card_x + card_w - b_box_w - 36
            draw.rounded_rectangle(
                [b_box_x, current_y, b_box_x + b_box_w, current_y + b_box_h],
                radius=6,
                fill=pal["badge_bg"],
                outline=pal["border_color"],
                width=1
            )
            draw.text((b_box_x + 12, current_y + 5), badge_str, fill=pal["badge_text"], font=font_badge)

        current_y += tag_box_h + 16

        # 2. Main Title (clipped if too wide)
        title_str = ov_data.title
        # Truncate if exceptionally long
        if len(title_str) > 42:
            title_str = title_str[:40] + "..."
        draw.text((card_x + 36, current_y), title_str, fill=pal["title_color"], font=font_title)
        current_y += font_title_size + 14

        # 3. Subtitle
        if ov_data.subtitle:
            sub_str = ov_data.subtitle
            if len(sub_str) > 65:
                sub_str = sub_str[:62] + "..."
            draw.text((card_x + 36, current_y), sub_str, fill=pal["subtitle_color"], font=font_sub)
            current_y += font_sub_size + 14

        # 4. Footer line
        if ov_data.footer:
            foot_str = ov_data.footer
            if len(foot_str) > 75:
                foot_str = foot_str[:72] + "..."
            draw.text((card_x + 36, current_y), foot_str, fill=pal["footer_color"], font=font_tag)

        # Save transparent overlay PNG
        temp_dir = temp_dir or settings.STORAGE_DIR / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        overlay_path = temp_dir / f"overlay_scene_{scene.scene_index}.png"
        try:
            overlay.save(overlay_path, format="PNG")
        finally:
            overlay.close()
        return overlay_path

    @classmethod
    def _prepare_base_image(
        cls,
        src_path: Path,
        target_w: int,
        target_h: int,
        scene_idx: int,
        temp_dir: Optional[Path] = None,
    ) -> Path:
        """
        Fits one source image to the target frame and writes a compact JPEG for FFmpeg.
        """
        temp_dir = temp_dir or settings.STORAGE_DIR / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        out_path = temp_dir / f"base_scene_{scene_idx}.jpg"

        with Image.open(src_path) as source_image:
            # draft() lets JPEG decoders reduce large sources before full decode.
            source_image.draft("RGB", (target_w, target_h))
            oriented = ImageOps.exif_transpose(source_image)
            try:
                fitted = ImageOps.fit(
                    oriented,
                    (target_w, target_h),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )
                try:
                    fitted.save(out_path, format="JPEG", quality=84, optimize=False, progressive=False)
                finally:
                    fitted.close()
            finally:
                if oriented is not source_image:
                    oriented.close()

        return out_path

    @staticmethod
    def _run_ffmpeg(command: List[str], stage: str, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        timeout_seconds = timeout or settings.FFMPEG_COMMAND_TIMEOUT_SECONDS
        started_at = time.monotonic()
        logger.info("FFmpeg stage '%s' starting (timeout=%ss)", stage, timeout_seconds)
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stderr = exc.stderr or ""
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            excerpt = stderr[-4000:]
            logger.error("FFmpeg stage '%s' timed out after %ss: %s", stage, timeout_seconds, excerpt)
            raise FFmpegExecutionError(
                f"FFmpeg {stage} timed out after {timeout_seconds} seconds. {excerpt}",
                timed_out=True,
            ) from exc
        except OSError as exc:
            logger.exception("Could not start FFmpeg stage '%s' using command %s", stage, command[0])
            raise FFmpegExecutionError(
                f"FFmpeg {stage} could not start: {exc}",
            ) from exc

        elapsed = time.monotonic() - started_at
        stderr = (result.stderr or "").strip()
        if result.returncode != 0:
            excerpt = stderr[-4000:] or "FFmpeg did not provide diagnostic output."
            logger.error("FFmpeg stage '%s' exited %s after %.1fs: %s", stage, result.returncode, elapsed, excerpt)
            raise FFmpegExecutionError(
                f"FFmpeg {stage} failed with exit code {result.returncode}. {excerpt}",
                returncode=result.returncode,
            )

        logger.info("FFmpeg stage '%s' completed in %.1fs (exit=%s)", stage, elapsed, result.returncode)
        if stderr:
            logger.debug("FFmpeg stage '%s' diagnostics: %s", stage, stderr[-2000:])
        return result

    @classmethod
    def render_video(
        cls,
        storyboard: StoryboardOutput,
        prop: PropertyInput,
        output_mp4: Path,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Executes complete FFmpeg video generation pipeline:
        1. Prepares base image and overlay graphics per scene.
        2. Renders scene MP4 clips with subtle Ken Burns zoom and translucent cards.
        3. Generates or acquires audio (voiceover + ambient background music).
        4. Concatenates video scenes and muxes audio with ducking and fade.
        5. Validates final MP4 format and returns comprehensive metadata.
        """
        ffmpeg_bin = settings.get_ffmpeg_path()
        logger.info("Starting video render: output=%s ffmpeg=%s", output_mp4, ffmpeg_bin)

        res_info = settings.RESOLUTIONS.get(prop.aspect_ratio.value, {"width": 1280, "height": 720})
        target_w = res_info["width"]
        target_h = res_info["height"]
        fps = settings.RENDER_FPS
        num_scenes = len(storyboard.scenes)
        if num_scenes == 0:
            raise ValueError("The storyboard has no scenes to render.")

        render_started_at = time.monotonic()
        render_deadline = render_started_at + settings.MAX_RENDER_JOB_SECONDS

        def timeout_for(stage: str, stage_limit: Optional[int] = None) -> int:
            remaining = render_deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"Video render exceeded its {settings.MAX_RENDER_JOB_SECONDS}-second time limit during {stage}."
                )
            limit = stage_limit or settings.FFMPEG_COMMAND_TIMEOUT_SECONDS
            return max(1, min(limit, int(remaining)))

        temp_dir = settings.STORAGE_DIR / "temp" / f"job_{output_mp4.stem}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_mp4.parent.mkdir(parents=True, exist_ok=True)
        staged_output = output_mp4.with_name(f".{output_mp4.stem}.{uuid.uuid4().hex}.partial.mp4")

        scene_video_clips: List[Path] = []

        try:
            logger.info(
                "Image processing stage started: %s scenes, %sx%s at %s FPS",
                num_scenes, target_w, target_h, fps,
            )
            for idx, scene in enumerate(storyboard.scenes):
                timeout_for(f"scene {idx + 1} image processing")
                if progress_callback:
                    pct = 30 + int((idx / num_scenes) * 35)
                    progress_callback(pct, f"Rendering scene {idx + 1} of {num_scenes} ({scene.scene_type})")

                base_img_path = None
                overlay_path = None
                scene_started_at = time.monotonic()
                try:
                    src_img_path = FileStorageService.get_image_path(scene.image_id)
                    if not src_img_path or not src_img_path.is_file():
                        raise FileNotFoundError(
                            f"Image for scene {idx + 1} with ID {scene.image_id} could not be found."
                        )

                    logger.info(
                        "Scene %s/%s image processing started: image=%s source_bytes=%s",
                        idx + 1, num_scenes, scene.image_id, src_img_path.stat().st_size,
                    )
                    base_img_path = cls._prepare_base_image(src_img_path, target_w, target_h, idx, temp_dir)
                    overlay_path = cls._create_scene_overlay(scene, prop, target_w, target_h, temp_dir)
                    logger.info(
                        "Scene %s/%s image processing completed: base_bytes=%s overlay_bytes=%s elapsed=%.1fs",
                        idx + 1,
                        num_scenes,
                        base_img_path.stat().st_size,
                        overlay_path.stat().st_size,
                        time.monotonic() - scene_started_at,
                    )

                    scene_clip_path = temp_dir / f"scene_{idx}.mp4"
                    duration_frames = max(1, int(round(scene.duration * fps)))
                    filter_complex = (
                        f"[0:v]zoompan=z='min(zoom+0.0008,1.06)':d={duration_frames}:"
                        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                        f"s={target_w}x{target_h}:fps={fps}[zoomed];"
                        "[zoomed][1:v]overlay=0:0:shortest=1[vout]"
                    )
                    thread_args = ["-filter_threads", "1", "-filter_complex_threads", "1"]
                    codec_args = [
                        "-c:v", "libx264", "-preset", "ultrafast", "-threads", "1",
                        "-pix_fmt", "yuv420p", "-r", str(fps),
                    ]
                    scene_inputs = [
                        ffmpeg_bin, "-hide_banner", "-loglevel", "warning", "-y",
                        *thread_args,
                        "-loop", "1", "-t", str(scene.duration), "-i", str(base_img_path),
                        "-loop", "1", "-t", str(scene.duration), "-i", str(overlay_path),
                        "-filter_complex", filter_complex,
                        "-map", "[vout]", *codec_args, str(scene_clip_path),
                    ]
                    try:
                        cls._run_ffmpeg(
                            scene_inputs,
                            f"scene {idx + 1} render",
                            timeout=timeout_for(f"scene {idx + 1} encoding"),
                        )
                    except FFmpegExecutionError as first_error:
                        if first_error.timed_out:
                            raise
                        logger.warning(
                            "Ken Burns scene render failed for scene %s; trying compatibility scale path: %s",
                            idx + 1, first_error,
                        )
                        fallback_filter = (
                            f"[0:v]scale={target_w}:{target_h}[scaled];"
                            "[scaled][1:v]overlay=0:0:shortest=1[vout]"
                        )
                        fallback_inputs = [
                            ffmpeg_bin, "-hide_banner", "-loglevel", "warning", "-y",
                            *thread_args,
                            "-loop", "1", "-t", str(scene.duration), "-i", str(base_img_path),
                            "-loop", "1", "-t", str(scene.duration), "-i", str(overlay_path),
                            "-filter_complex", fallback_filter,
                            "-map", "[vout]", *codec_args, str(scene_clip_path),
                        ]
                        cls._run_ffmpeg(
                            fallback_inputs,
                            f"scene {idx + 1} compatibility render",
                            timeout=timeout_for(f"scene {idx + 1} compatibility encoding"),
                        )
                    scene_video_clips.append(scene_clip_path)
                    logger.info(
                        "Scene %s/%s completed in %.1fs: clip_bytes=%s",
                        idx + 1, num_scenes, time.monotonic() - scene_started_at, scene_clip_path.stat().st_size,
                    )
                finally:
                    for temporary_image in (base_img_path, overlay_path):
                        if temporary_image is not None:
                            temporary_image.unlink(missing_ok=True)
                    logger.info("Released scene %s image and overlay resources", idx + 1)

            if progress_callback:
                progress_callback(70, "Concatenating scenes and composing audio tracks")

            logger.info("Scene concatenation stage started: %s clips", len(scene_video_clips))
            concat_txt_path = temp_dir / "concat_list.txt"
            with open(concat_txt_path, "w", encoding="utf-8") as f:
                for sc in scene_video_clips:
                    # FFmpeg concat demuxer requires forward slashes or escaped backslashes
                    clean_path = str(sc).replace("\\", "/")
                    f.write(f"file '{clean_path}'\n")
            logger.info("Scene concatenation input prepared: %s clips; no intermediate combined video created", len(scene_video_clips))

            # Step 3: Audio synthesis and mixing
            if progress_callback:
                progress_callback(80, "Mixing voiceover and ambient soundtrack")

            voiceover_tracks: List[Tuple[Path, float, float, float]] = []
            if prop.narration_enabled and settings.TTS_PROVIDER != "none":
                logger.info("Narration generation stage started")
                scene_start = 0.0
                for idx, scene in enumerate(storyboard.scenes):
                    text = scene.voiceover_text.strip()
                    if text:
                        vo_temp = temp_dir / f"voiceover_scene_{idx}.mp3"
                        narration_started_at = time.monotonic()
                        logger.info("Narration generation started for scene %s/%s", idx + 1, num_scenes)
                        vo_path = asyncio.run(
                            asyncio.wait_for(
                                AudioService.generate_voiceover(
                                    text,
                                    vo_temp,
                                    voice=getattr(prop, "voice_accent", None)
                                ),
                                timeout=timeout_for("narration", settings.TTS_GENERATION_TIMEOUT_SECONDS),
                            )
                        )
                        if not vo_path or not vo_path.is_file() or vo_path.stat().st_size <= 500:
                            selected_voice = getattr(prop, "voice_accent", "en-US-BrianNeural")
                            raise RuntimeError(
                                f"Narration could not be generated for {selected_voice}. "
                                "Check the internet connection or install a matching English system speech voice."
                            )
                        audio_duration = cls._probe_audio_duration(
                            vo_path,
                            ffmpeg_bin,
                            timeout=timeout_for("narration audio probe", 30),
                        ) or scene.duration
                        voiceover_tracks.append((vo_path, scene_start, audio_duration, scene.duration))
                        logger.info(
                            "Narration generation completed for scene %s/%s in %.1fs: bytes=%s duration=%.2fs",
                            idx + 1, num_scenes, time.monotonic() - narration_started_at,
                            vo_path.stat().st_size, audio_duration,
                        )
                    scene_start += scene.duration

                if not voiceover_tracks:
                    raise RuntimeError("The script has no scene narration to synthesize.")
                logger.info("Narration generation completed: %s tracks", len(voiceover_tracks))
            else:
                logger.info("Narration generation skipped: narration is disabled")

            logger.info(
                "Audio mixing stage started: narration_tracks=%s music_enabled=%s",
                len(voiceover_tracks), prop.music_enabled,
            )
            bg_music_path = AudioService.get_background_music_path() if prop.music_enabled else None
            if prop.music_enabled and bg_music_path:
                logger.info("Background music available: %s (%s bytes)", bg_music_path, bg_music_path.stat().st_size)
            elif prop.music_enabled:
                logger.warning("Background music was requested but no bundled music file is available")

            # Step 4: Final Muxing
            if progress_callback:
                progress_callback(90, "Aligning scene narration and finalizing MP4")

            total_dur = storyboard.total_duration
            final_cmd = [
                ffmpeg_bin, "-hide_banner", "-loglevel", "warning", "-y",
                "-filter_threads", "1", "-filter_complex_threads", "1", "-threads", "1",
                "-f", "concat", "-safe", "0", "-i", str(concat_txt_path),
            ]
            voice_input_indexes = []
            for vo_path, _, _, _ in voiceover_tracks:
                voice_input_indexes.append(1 + len(voice_input_indexes))
                final_cmd.extend(["-i", str(vo_path)])

            bg_music_index = None
            if bg_music_path:
                bg_music_index = 1 + len(voice_input_indexes)
                final_cmd.extend(["-stream_loop", "-1", "-i", str(bg_music_path)])

            audio_filters = []
            voice_labels = []
            mix_input_count = len(voiceover_tracks) + (1 if bg_music_index is not None else 0)
            for track_index, (input_index, track) in enumerate(zip(voice_input_indexes, voiceover_tracks)):
                _, scene_start, audio_duration, scene_duration = track
                usable_duration = max(0.25, scene_duration - 0.15)
                speed_factor = max(1.0, audio_duration / usable_duration)
                tempo_filters = []
                while speed_factor > 2.0:
                    tempo_filters.append("atempo=2.0")
                    speed_factor /= 2.0
                if speed_factor > 1.01:
                    tempo_filters.append(f"atempo={speed_factor:.3f}")
                tempo_chain = ",".join(tempo_filters)
                if tempo_chain:
                    tempo_chain += ","
                delay_ms = max(0, round(scene_start * 1000))
                label = f"vo{track_index}"
                voice_labels.append(f"[{label}]")
                audio_filters.append(
                    f"[{input_index}:a]{tempo_chain}aformat=sample_rates=44100:channel_layouts=stereo,"
                    f"volume={1.2 * mix_input_count:.3f},adelay={delay_ms}|{delay_ms},"
                    f"apad,atrim=duration={total_dur}[{label}]"
                )

            if bg_music_index is not None:
                music_start = max(0, total_dur - 2.5)
                music_volume = 0.18 * mix_input_count if voice_labels else 0.35
                audio_filters.append(
                    f"[{bg_music_index}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                    f"volume={music_volume:.3f},atrim=duration={total_dur},afade=t=in:ss=0:d=1,"
                    f"afade=t=out:st={music_start}:d=2.5[bg]"
                )
                if voice_labels:
                    audio_filters.append(
                        f"[bg]{''.join(voice_labels)}amix=inputs={len(voice_labels) + 1}:"
                        "duration=first:dropout_transition=0[mixed];[mixed]volume=0.8[aout]"
                    )
                else:
                    audio_filters.append("[bg]anull[aout]")
            elif len(voice_labels) == 1:
                audio_filters.append(f"{voice_labels[0]}volume=0.8[aout]")
            elif voice_labels:
                audio_filters.append(
                    f"{''.join(voice_labels)}amix=inputs={len(voice_labels)}:"
                    "duration=first:dropout_transition=0[mixed];[mixed]volume=0.8[aout]"
                )

            if audio_filters:
                final_cmd.extend([
                    "-filter_complex", ";".join(audio_filters),
                    "-map", "0:v",
                    "-map", "[aout]"
                ])
            else:
                # Silent MP4 -> Generate null stereo audio so players don't error
                final_cmd.extend([
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-map", "0:v",
                    "-map", "1:a"
                ])

            final_cmd.extend([
                "-t", str(total_dur),
                "-c:v", "copy",
                "-c:a", "aac",
                "-threads", "1",
                "-b:a", "192k",
                "-movflags", "+faststart",
                str(staged_output)
            ])

            logger.info("Audio mixing and final mux stage started")
            cls._run_ffmpeg(final_cmd, "audio mix and final mux", timeout=timeout_for("audio mixing"))
            logger.info("Audio mixing and final mux completed: staged_bytes=%s", staged_output.stat().st_size)

            if not staged_output.is_file() or staged_output.stat().st_size < 1000:
                raise RuntimeError("FFmpeg exited successfully but did not create a usable MP4 output file.")
            with staged_output.open("rb") as mp4_file:
                mp4_header = mp4_file.read(12)
            if len(mp4_header) < 8 or mp4_header[4:8] != b"ftyp":
                raise RuntimeError("FFmpeg output is not a valid MP4 container (missing ftyp signature).")

            cls._run_ffmpeg(
                [
                    ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-xerror", "-threads", "1",
                    "-i", str(staged_output), "-f", "null", "-",
                ],
                "final MP4 decode validation",
                timeout=timeout_for("final MP4 validation", 60),
            )

            os.replace(staged_output, output_mp4)
            logger.info("Final MP4 file created and validated: %s (%s bytes)", output_mp4, output_mp4.stat().st_size)
            for scene_clip in scene_video_clips:
                scene_clip.unlink(missing_ok=True)
            concat_txt_path.unlink(missing_ok=True)
            logger.info("Released temporary scene clips and concat list")

            file_size = output_mp4.stat().st_size

            return {
                "duration_seconds": total_dur,
                "width": target_w,
                "height": target_h,
                "file_size_bytes": file_size,
                "format": "mp4",
                "fps": fps,
                "aspect_ratio": prop.aspect_ratio.value
            }

        except Exception:
            staged_output.unlink(missing_ok=True)
            logger.exception("Video render failed for output %s", output_mp4)
            raise
        finally:
            logger.info("Cleaning temporary render directory: %s", temp_dir)
            try:
                shutil.rmtree(temp_dir)
            except FileNotFoundError:
                pass
            except OSError:
                logger.exception("Could not completely clean temporary render directory %s", temp_dir)
