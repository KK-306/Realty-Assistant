from typing import List, Dict, Any
from app.models.property import PropertyInput, VisualTheme
from app.models.storyboard import StoryboardOutput, StoryboardScene, SceneOverlay, ScriptOutput
from app.services.script_generator import ScriptGenerator
from app.services.gemini_image_service import GeminiImageService
from app.services.file_storage import FileStorageService

class StoryboardService:
    @classmethod
    def generate_storyboard(cls, prop: PropertyInput) -> StoryboardOutput:
        """
        Creates a structured storyboard from uploaded photos and fills missing scenes
        with illustrative Gemini-generated images when fewer than four were supplied.
        """
        # Step 1: Generate or retrieve script
        script_dict = ScriptGenerator.generate(prop)
        script_output = ScriptOutput(
            video_title=script_dict["video_title"],
            opening_hook=script_dict["opening_hook"],
            voiceover_full=script_dict["voiceover_full"],
            closing_cta=script_dict["closing_cta"],
            scene_voiceovers=script_dict["scene_voiceovers"]
        )

        image_ids = list(prop.image_ids)
        generated_image_ids = set()
        if len(image_ids) < 4:
            if not GeminiImageService.is_available():
                raise ValueError(
                    "Upload at least 4 photos, or configure Gemini in the backend to generate the missing scene images."
                )
            for scene_index in range(len(image_ids), 4):
                image_bytes, content_type = GeminiImageService.generate_concept_image(
                    cls._image_prompt(
                        prop,
                        scene_index,
                        script_dict["scene_voiceovers"][scene_index],
                    ),
                    prop.aspect_ratio.value,
                )
                saved_image = FileStorageService.validate_and_save_image(
                    file_bytes=image_bytes,
                    original_filename=f"gemini_concept_scene_{scene_index + 1}.png",
                    content_type=content_type,
                )
                image_ids.append(saved_image["image_id"])
                generated_image_ids.add(saved_image["image_id"])

        num_scenes = len(image_ids)
        total_duration = float(prop.duration)
        
        # Calculate per-scene duration
        base_scene_duration = round(total_duration / num_scenes, 2)
        
        # Prepare scene durations ensuring sum == total_duration
        durations = [base_scene_duration] * num_scenes
        current_sum = sum(durations)
        diff = round(total_duration - current_sum, 2)
        durations[-1] = round(durations[-1] + diff, 2)

        # Theme badges & tags
        theme_tags = {
            VisualTheme.LUXURY: "LUXURY RESIDENCE",
            VisualTheme.MODERN: "MODERN LIVING",
            VisualTheme.MINIMAL: "ESSENTIAL LIVING",
            VisualTheme.ELEGANT: "ELEGANT PROPERTY"
        }
        main_tag = theme_tags.get(prop.theme, "FEATURED PROPERTY")

        price_str = prop.price_display or f"{prop.currency}{prop.price:,.0f}"
        prop_type_label = prop.property_type.value.replace("_", " ").title()

        spec_parts = []
        if prop.bedrooms:
            spec_parts.append(f"{prop.bedrooms} Bed{'s' if prop.bedrooms > 1 else ''}")
        if prop.bathrooms:
            spec_parts.append(f"{prop.bathrooms} Bath{'s' if prop.bathrooms > 1 else ''}")
        specs_label = " • ".join(spec_parts) if spec_parts else prop_type_label

        features = list(prop.key_features)
        scenes: List[StoryboardScene] = []

        for idx, (img_id, duration) in enumerate(zip(image_ids, durations)):
            if idx == 0:
                # Opening Scene
                scene_type = "opening"
                caption = f"{prop.property_name} • {prop.location}"
                overlay = SceneOverlay(
                    tag=main_tag,
                    title=prop.property_name,
                    subtitle=f"{prop_type_label} in {prop.location}",
                    badge=price_str,
                    footer=f"{specs_label}" if spec_parts else prop.location
                )
            elif idx == num_scenes - 1:
                # Closing Scene
                scene_type = "closing"
                caption = f"{prop.cta_text} • {prop.contact_details or prop.contact_name}"
                overlay = SceneOverlay(
                    tag="SCHEDULE YOUR VISIT",
                    title=prop.cta_text,
                    subtitle=prop.contact_details or "Inquire for details & private viewing",
                    badge=price_str,
                    footer=f"Agent: {prop.contact_name or 'Sales Team'}"
                )
            elif idx == 1:
                # Property Highlights / Specs scene
                scene_type = "highlight"
                caption = f"{specs_label} • Offered at {price_str}"
                feat_text = features[0] if features else prop_type_label
                overlay = SceneOverlay(
                    tag="PROPERTY HIGHLIGHT",
                    title=specs_label,
                    subtitle=f"Offered at {price_str}",
                    badge=price_str,
                    footer=feat_text
                )
            else:
                # Feature scenes
                scene_type = "feature"
                feat_idx = (idx - 2) % len(features) if features else 0
                feat_name = features[feat_idx] if features else "Exceptional Design"
                caption = feat_name
                overlay = SceneOverlay(
                    tag=f"FEATURE {idx}",
                    title=feat_name,
                    subtitle=f"Designed for comfort and style",
                    badge=price_str,
                    footer=prop.property_name
                )

            if img_id in generated_image_ids:
                overlay.tag = "AI CONCEPT"

            scenes.append(
                StoryboardScene(
                    scene_index=idx,
                    scene_type=scene_type,
                    duration=duration,
                    image_id=img_id,
                    image_index=idx,
                    generated_image=img_id in generated_image_ids,
                    caption=caption,
                    voiceover_text=script_dict["scene_voiceovers"][idx],
                    overlay=overlay
                )
            )

        return StoryboardOutput(
            script=script_output,
            scenes=scenes,
            total_duration=total_duration,
            aspect_ratio=prop.aspect_ratio.value,
            theme=prop.theme.value
        )

    @staticmethod
    def _image_prompt(prop: PropertyInput, scene_index: int, voiceover_line: str = "") -> str:
        property_type = prop.property_type.value.replace("_", " ")
        theme = prop.theme.value
        feature = prop.key_features[(scene_index - 2) % len(prop.key_features)] if prop.key_features else ""

        if scene_index == 3:
            scene_idea = f"a calm closing wide shot of a generic {property_type} concept"
        elif prop.property_type.value == "plot":
            plot_views = [
                "a wide establishing view of an undeveloped plot of land",
                "a ground-level view across a clearly undeveloped parcel",
                "a calm architectural study of open land and its natural surroundings",
                "a detail view of the ground and boundary line of an undeveloped parcel",
            ]
            scene_idea = plot_views[scene_index % len(plot_views)]
        elif prop.property_type.value == "commercial":
            commercial_views = [
                "a polished commercial property exterior",
                "a bright, flexible professional workspace concept",
                "a refined architectural detail of a commercial property",
                f"a cinematic commercial design detail inspired by the verified feature: {feature}",
            ]
            scene_idea = commercial_views[scene_index % len(commercial_views)]
        elif scene_index == 0:
            scene_idea = f"a tasteful architectural exterior concept for a {property_type}"
        elif scene_index == 1:
            scene_idea = f"a welcoming interior space for a {property_type}"
        elif scene_index == 2:
            scene_idea = f"a refined architectural detail or interior for a {property_type}"
        else:
            scene_idea = f"a cinematic detail shot inspired by the verified property feature: {feature}"

        return (
            f"Create a photorealistic, high-end real-estate editorial concept image: {scene_idea}. "
            f"Use a {theme} visual style, natural materials, balanced composition, and soft cinematic lighting. "
            f"The listing is located in {prop.location}; use this only as broad visual context. "
            f"This scene accompanies the narration: {voiceover_line}. Reflect its property detail visually, without rendering words. "
            "This is an illustrative concept, not a photograph of the exact listed property. Do not add specific amenities, views, signage, text, logos, people, or claims. "
            "Create a clean, believable architectural photograph suitable as background footage for a property showcase video."
        )
