import json
import logging
from typing import Dict, Any, List, Optional
import httpx

from app.config import settings
from app.models.property import PropertyInput, VisualTheme
from app.models.storyboard import ScriptOutput

logger = logging.getLogger(__name__)

class ScriptGenerator:
    """
    Generates promotional property scripts grounded strictly in user-provided facts.
    Supports LLM providers (Gemini, OpenAI, Groq) with an automatic deterministic fallback.
    """

    @classmethod
    def generate(cls, prop: PropertyInput) -> Dict[str, Any]:
        """
        Attempts LLM generation if configured, otherwise immediately uses
        the deterministic template generator.
        """
        if settings.LLM_PROVIDER != "template" and settings.LLM_API_KEY:
            try:
                llm_result = cls._call_llm(prop)
                if llm_result:
                    return llm_result
            except Exception as e:
                logger.warning(f"LLM generation failed: {e}. Falling back to deterministic generator.")
                
        # Deterministic factual fallback
        return cls._generate_deterministic(prop)

    @classmethod
    def _call_llm(cls, prop: PropertyInput) -> Optional[Dict[str, Any]]:
        """
        Calls external LLM with strict factual grounding instructions.
        """
        system_prompt = (
            "You are a factual real estate promotional scriptwriter. "
            "CRITICAL FACTUALITY RULES:\n"
            "1. ONLY use the explicit facts provided in the prompt.\n"
            "2. NEVER invent amenities, distances, square footage, landmark proximity, legal statuses, or unmentioned features.\n"
            "3. If a detail (like bedrooms or bathrooms) is not provided, DO NOT mention or infer it.\n"
            "4. Output STRICT JSON conforming to the requested schema with no surrounding markdown or explanation."
        )

        user_content = {
            "property_name": prop.property_name,
            "location": prop.location,
            "price_display": prop.price_display or f"{prop.currency}{prop.price:,.0f}",
            "property_type": prop.property_type.value,
            "key_features": prop.key_features,
            "bedrooms": prop.bedrooms,
            "bathrooms": prop.bathrooms,
            "description": prop.description,
            "cta_text": prop.cta_text,
            "theme": prop.theme.value,
            "duration_seconds": prop.duration
        }

        schema_instruction = (
            "Return a JSON object with this exact schema:\n"
            "{\n"
            '  "video_title": "string",\n'
            '  "opening_hook": "string",\n'
            '  "voiceover_full": "string",\n'
            '  "closing_cta": "string",\n'
            '  "scene_captions": ["caption for scene 1", "caption for scene 2", ...]\n'
            "}"
        )

        prompt_str = f"{system_prompt}\n\nProperty Details:\n{json.dumps(user_content, indent=2)}\n\n{schema_instruction}"

        # Gemini REST call
        if settings.LLM_PROVIDER == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.LLM_MODEL}:generateContent?key={settings.LLM_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt_str}]}],
                "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"}
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(text)
                    return cls._validate_and_sanitize_script(parsed, prop)

        # OpenAI / Groq REST call
        elif settings.LLM_PROVIDER in ("openai", "groq"):
            endpoint = (
                "https://api.openai.com/v1/chat/completions"
                if settings.LLM_PROVIDER == "openai"
                else "https://api.groq.com/openai/v1/chat/completions"
            )
            model = settings.LLM_MODEL if settings.LLM_PROVIDER == "openai" else "llama-3.1-70b-versatile"
            headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{json.dumps(user_content)}\n{schema_instruction}"}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post(endpoint, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    text = data["choices"][0]["message"]["content"]
                    parsed = json.loads(text)
                    return cls._validate_and_sanitize_script(parsed, prop)

        return None

    @classmethod
    def _validate_and_sanitize_script(cls, data: Dict[str, Any], prop: PropertyInput) -> Dict[str, Any]:
        """
        Ensures all required fields exist and ensures no empty values.
        """
        required_keys = ["video_title", "opening_hook", "voiceover_full", "closing_cta", "scene_captions"]
        for k in required_keys:
            if k not in data or not data[k]:
                raise ValueError(f"Missing required key in generated script: {k}")

        # Check that scene captions is a list
        if not isinstance(data["scene_captions"], list) or len(data["scene_captions"]) < 2:
            raise ValueError("Scene captions must be a non-empty list of at least 2 captions.")

        return {
            "video_title": str(data["video_title"]).strip(),
            "opening_hook": str(data["opening_hook"]).strip(),
            "voiceover_full": str(data["voiceover_full"]).strip(),
            "closing_cta": str(data["closing_cta"]).strip(),
            "scene_captions": [str(c).strip() for c in data["scene_captions"] if str(c).strip()]
        }

    @classmethod
    def _generate_deterministic(cls, prop: PropertyInput) -> Dict[str, Any]:
        """
        Deterministic, strictly factual script generator.
        Never invents features, sizes, or unsupported facts.
        Adapts vocabulary to the selected VisualTheme.
        """
        price_str = prop.price_display or f"{prop.currency}{prop.price:,.0f}"
        prop_type_label = prop.property_type.value.replace("_", " ").title()
        
        # Spec phrase: only if bedrooms/bathrooms are provided
        spec_parts = []
        if prop.bedrooms:
            spec_parts.append(f"{prop.bedrooms} Bedroom{'s' if prop.bedrooms > 1 else ''}")
        if prop.bathrooms:
            spec_parts.append(f"{prop.bathrooms} Bath{'s' if prop.bathrooms > 1 else ''}")
        spec_str = " • ".join(spec_parts) if spec_parts else prop_type_label

        theme_styles = {
            VisualTheme.LUXURY: {
                "hook_prefix": "Welcome to an extraordinary residence at",
                "closing_lead": "Exclusive opportunities await at",
                "tagline": "Refined Living Defined"
            },
            VisualTheme.MODERN: {
                "hook_prefix": "Discover contemporary urban living at",
                "closing_lead": "Experience intelligent modern living at",
                "tagline": "Modern Spaces, Elevated Living"
            },
            VisualTheme.MINIMAL: {
                "hook_prefix": "Step inside the thoughtfully designed spaces of",
                "closing_lead": "Pure design and clarity at",
                "tagline": "Essential Spaces, Perfectly Crafted"
            },
            VisualTheme.ELEGANT: {
                "hook_prefix": "Presenting the gracious architectural design of",
                "closing_lead": "Timeless charm and enduring value at",
                "tagline": "Timeless Elegance & Warmth"
            }
        }
        style = theme_styles.get(prop.theme, theme_styles[VisualTheme.LUXURY])

        video_title = f"{prop.property_name} | {prop.location}"
        opening_hook = f"{style['hook_prefix']} {prop.property_name}, {prop.location}."
        
        # Build scene captions from provided verified features
        captions: List[str] = []
        
        # Scene 1: Opening hook & property identity
        captions.append(f"{prop.property_name} — {prop_type_label} in {prop.location}")
        
        # Scene 2: Specs & price
        if spec_parts:
            captions.append(f"{spec_str} • Offered at {price_str}")
        else:
            captions.append(f"Offered at {price_str} • {prop.location}")
            
        # Subsequent scenes: One or two features per scene
        features = prop.key_features
        for idx, feat in enumerate(features):
            captions.append(f"{feat.strip()}")
            
        # Closing Scene: Call to Action
        contact_line = prop.contact_details or prop.contact_name or "Contact sales team"
        captions.append(f"{prop.cta_text} — {contact_line}")

        # Assemble full voiceover script strictly using these facts
        vo_sentences = [
            f"Welcome to {prop.property_name}, situated in {prop.location}."
        ]
        if spec_parts:
            vo_sentences.append(f"This {prop_type_label.lower()} offers {spec_str}, priced at {price_str}.")
        else:
            vo_sentences.append(f"This {prop_type_label.lower()} is available for {price_str}.")
            
        if features:
            feature_text = ", ".join(features[:4])
            vo_sentences.append(f"Highlights include {feature_text}.")
            
        vo_sentences.append(f"{prop.cta_text}. Contact {prop.contact_name or 'our team'} today.")
        
        voiceover_full = " ".join(vo_sentences)
        closing_cta = f"{prop.cta_text} • {contact_line}"

        return {
            "video_title": video_title,
            "opening_hook": opening_hook,
            "voiceover_full": voiceover_full,
            "closing_cta": closing_cta,
            "scene_captions": captions
        }
