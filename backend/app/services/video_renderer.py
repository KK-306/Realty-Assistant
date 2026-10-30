import os
import asyncio
import subprocess
import shutil
import logging
import math
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from app.config import settings
from app.models.property import PropertyInput, VisualTheme
from app.models.storyboard import StoryboardOutput, StoryboardScene
from app.services.file_storage import FileStorageService
from app.services.audio_service import AudioService

logger = logging.getLogger(__name__)

class VideoRenderer:
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
        target_h: int
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
        temp_dir = settings.STORAGE_DIR / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        overlay_path = temp_dir / f"overlay_scene_{scene.scene_index}.png"
        overlay.save(overlay_path, format="PNG")
        return overlay_path

    @classmethod
    def _prepare_base_image(cls, src_path: Path, target_w: int, target_h: int, scene_idx: int) -> Path:
        """
        Scales and center-crops the user image to the target dimensions without distortion,
        saving as a clean temp image for FFmpeg zoompan.
        """
        temp_dir = settings.STORAGE_DIR / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        out_path = temp_dir / f"base_scene_{scene_idx}.jpg"

        with Image.open(src_path) as img:
            img = img.convert("RGB")
            src_w, src_h = img.size
            src_ratio = src_w / src_h
            target_ratio = target_w / target_h

            if src_ratio > target_ratio:
                # Source is wider: match height, crop width
                new_h = target_h
                new_w = int(target_h * src_ratio)
            else:
                # Source is taller: match width, crop height
                new_w = target_w
                new_h = int(target_w / src_ratio)

            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            # Center crop
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            cropped = resized.crop((left, top, left + target_w, top + target_h))
            cropped.save(out_path, quality=95)

        return out_path

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
        logger.info(f"Using FFmpeg binary: {ffmpeg_bin}")

        res_info = settings.RESOLUTIONS.get(prop.aspect_ratio.value, {"width": 1920, "height": 1080})
        target_w = res_info["width"]
        target_h = res_info["height"]
        fps = 30

        temp_dir = settings.STORAGE_DIR / "temp" / f"job_{output_mp4.stem}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        scene_video_clips: List[Path] = []
        num_scenes = len(storyboard.scenes)

        try:
            # Step 1: Render each scene video clip
            for idx, scene in enumerate(storyboard.scenes):
                if progress_callback:
                    pct = 30 + int((idx / num_scenes) * 35)
                    progress_callback(pct, f"Rendering scene {idx + 1} of {num_scenes} ({scene.scene_type})")

                # Resolve image
                src_img_path = FileStorageService.get_image_path(scene.image_id)
                if not src_img_path or not src_img_path.is_file():
                    raise FileNotFoundError(f"Image for scene {idx} with ID {scene.image_id} could not be found.")

                # Prepare base image
                base_img_path = cls._prepare_base_image(src_img_path, target_w, target_h, idx)
                # Render overlay card
                overlay_path = cls._create_scene_overlay(scene, prop, target_w, target_h)

                scene_clip_path = temp_dir / f"scene_{idx}.mp4"
                duration_frames = int(scene.duration * fps)

                # Ken Burns effect: subtle zoom in from 1.0 to 1.06
                # zoompan with overlay filter in FFmpeg
                # For maximum reliability and speed on all FFmpeg builds:
                # [0:v]zoompan=z='min(zoom+0.0006,1.06)':d={duration_frames}:s={target_w}x{target_h}:fps={fps}[zoomed];
                # [zoomed][1:v]overlay=0:0[vout]
                filter_complex = (
                    f"[0:v]zoompan=z='min(zoom+0.0008,1.06)':d={duration_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={target_w}x{target_h}:fps={fps}[zoomed];"
                    f"[zoomed][1:v]overlay=0:0:shortest=1[vout]"
                )

                cmd = [
                    ffmpeg_bin,
                    "-y",
                    "-loop", "1",
                    "-t", str(scene.duration),
                    "-i", str(base_img_path),
                    "-loop", "1",
                    "-t", str(scene.duration),
                    "-i", str(overlay_path),
                    "-filter_complex", filter_complex,
                    "-map", "[vout]",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-preset", "fast",
                    "-r", str(fps),
                    str(scene_clip_path)
                ]

                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode != 0:
                    logger.error(f"FFmpeg scene {idx} render failed: {res.stderr}")
                    # If zoompan had any issue on older builds, fallback to direct scale + overlay
                    fallback_filter = f"[0:v]scale={target_w}:{target_h}[scaled];[scaled][1:v]overlay=0:0:shortest=1[vout]"
                    fallback_cmd = [
                        ffmpeg_bin,
                        "-y",
                        "-loop", "1",
                        "-t", str(scene.duration),
                        "-i", str(base_img_path),
                        "-loop", "1",
                        "-t", str(scene.duration),
                        "-i", str(overlay_path),
                        "-filter_complex", fallback_filter,
                        "-map", "[vout]",
                        "-c:v", "libx264",
                        "-pix_fmt", "yuv420p",
                        "-preset", "fast",
                        "-r", str(fps),
                        str(scene_clip_path)
                    ]
                    res2 = subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if res2.returncode != 0:
                        raise RuntimeError(f"FFmpeg failed to render scene clip {idx}: {res2.stderr}")

                scene_video_clips.append(scene_clip_path)

            if progress_callback:
                progress_callback(70, "Concatenating scenes and composing audio tracks")

            # Step 2: Concatenate all scene clips into combined video
            concat_txt_path = temp_dir / "concat_list.txt"
            with open(concat_txt_path, "w", encoding="utf-8") as f:
                for sc in scene_video_clips:
                    # FFmpeg concat demuxer requires forward slashes or escaped backslashes
                    clean_path = str(sc).replace("\\", "/")
                    f.write(f"file '{clean_path}'\n")

            combined_video_path = temp_dir / "combined_video.mp4"
            concat_cmd = [
                ffmpeg_bin,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_txt_path),
                "-c:v", "copy",
                str(combined_video_path)
            ]
            concat_res = subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if concat_res.returncode != 0:
                raise RuntimeError(f"FFmpeg failed to concatenate scenes: {concat_res.stderr}")

            # Step 3: Audio synthesis and mixing
            if progress_callback:
                progress_callback(80, "Mixing voiceover and ambient soundtrack")

            vo_path = None
            if prop.narration_enabled and settings.TTS_PROVIDER != "none":
                vo_temp = temp_dir / "voiceover.mp3"
                vo_path = asyncio.run(
                    AudioService.generate_voiceover(
                        storyboard.script.voiceover_full,
                        vo_temp,
                        voice=getattr(prop, "voice_accent", None)
                    )
                )
                if not vo_path or not vo_path.is_file() or vo_path.stat().st_size <= 500:
                    selected_voice = getattr(prop, "voice_accent", "en-US-BrianNeural")
                    raise RuntimeError(
                        f"Narration could not be generated for {selected_voice}. "
                        "Check the internet connection or install a matching English system speech voice."
                    )

            bg_music_path = AudioService.get_background_music_path() if prop.music_enabled else None

            # Step 4: Final Muxing
            if progress_callback:
                progress_callback(90, "Finalizing MP4 video container")

            total_dur = storyboard.total_duration

            # Build final FFmpeg mux command depending on audio tracks available
            final_cmd = [ffmpeg_bin, "-y", "-i", str(combined_video_path)]

            if vo_path and bg_music_path:
                # Both Narration and Background Music -> Mix with professional vocal presence and subtle ducking
                final_cmd.extend([
                    "-stream_loop", "-1", "-i", str(bg_music_path),
                    "-i", str(vo_path),
                    "-filter_complex",
                    f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.18,afade=t=in:ss=0:d=1,afade=t=out:st={total_dur - 2.5}:d=2.5[bg];"
                    f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.25[vo];"
                    f"[bg][vo]amix=inputs=2:duration=first:dropout_transition=2[aout]",
                    "-map", "0:v",
                    "-map", "[aout]"
                ])
            elif bg_music_path:
                # Background Music Only -> Fade in/out
                final_cmd.extend([
                    "-stream_loop", "-1", "-i", str(bg_music_path),
                    "-filter_complex",
                    f"[1:a]volume=0.35,afade=t=in:ss=0:d=1,afade=t=out:st={total_dur - 2.5}:d=2.5[aout]",
                    "-map", "0:v",
                    "-map", "[aout]"
                ])
            elif vo_path:
                # Narration Only
                final_cmd.extend([
                    "-i", str(vo_path),
                    "-map", "0:v",
                    "-map", "1:a"
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
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                str(output_mp4)
            ])

            final_res = subprocess.run(final_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if final_res.returncode != 0:
                raise RuntimeError(f"FFmpeg final muxing failed: {final_res.stderr}")

            # Step 5: Validate rendered MP4
            if not output_mp4.is_file() or output_mp4.stat().st_size < 1000:
                raise RuntimeError("Generated MP4 file is empty or corrupted.")

            file_size = output_mp4.stat().st_size
            logger.info(f"Successfully generated video: {output_mp4} ({file_size} bytes)")

            return {
                "duration_seconds": total_dur,
                "width": target_w,
                "height": target_h,
                "file_size_bytes": file_size,
                "format": "mp4",
                "fps": fps,
                "aspect_ratio": prop.aspect_ratio.value
            }

        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
