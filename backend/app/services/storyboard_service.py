from typing import List, Dict, Any
from app.models.property import PropertyInput, VisualTheme
from app.models.storyboard import StoryboardOutput, StoryboardScene, SceneOverlay, ScriptOutput
from app.services.script_generator import ScriptGenerator

class StoryboardService:
    @classmethod
    def generate_storyboard(cls, prop: PropertyInput) -> StoryboardOutput:
        """
        Creates a structured storyboard matching the exact number of uploaded images (4-8)
        and pacing each scene so that total duration matches the requested 20, 30, or 40 seconds.
        """
        # Step 1: Generate or retrieve script
        script_dict = ScriptGenerator.generate(prop)
        script_output = ScriptOutput(
            video_title=script_dict["video_title"],
            opening_hook=script_dict["opening_hook"],
            voiceover_full=script_dict["voiceover_full"],
            closing_cta=script_dict["closing_cta"]
        )

        image_ids = prop.image_ids
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
                vo = f"Welcome to {prop.property_name}, {prop.location}."
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
                vo = f"{prop.cta_text}. Contact {prop.contact_name or 'our sales team'} today."
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
                vo = f"Offered at {price_str}, featuring {specs_label}."
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
                vo = f"Highlighting {feat_name.lower()}."
                overlay = SceneOverlay(
                    tag=f"FEATURE {idx}",
                    title=feat_name,
                    subtitle=f"Designed for comfort and style",
                    badge=price_str,
                    footer=prop.property_name
                )

            scenes.append(
                StoryboardScene(
                    scene_index=idx,
                    scene_type=scene_type,
                    duration=duration,
                    image_id=img_id,
                    image_index=idx,
                    caption=caption,
                    voiceover_text=vo,
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
