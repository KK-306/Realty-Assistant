"""
Asset generator for demo real estate photos and royalty-free ambient audio.
Creates 6 high-resolution (1920x1080) real estate demonstration images
and a 30-second seamless ambient piano/pad soundtrack.
"""

import os
import math
import struct
import wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_IMG_DIR = os.path.join(ASSETS_DIR, "sample_properties")
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
os.makedirs(SAMPLE_IMG_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

def create_ambient_track(filename="ambient_lounge.wav", duration_sec=35, sample_rate=44100):
    """
    Synthesize a warm, lush, ambient chord progression suitable for real estate promo videos.
    Uses soft sinusoidal harmonics, chorused pads, and gentle decay.
    """
    output_path = os.path.join(AUDIO_DIR, filename)
    num_samples = int(duration_sec * sample_rate)
    
    # Chord frequencies: Cmaj9 -> Am9 -> Fmaj7 -> Gsus4 (warm real estate ambient progression)
    # 4 bars looped
    chords = [
        [130.81, 164.81, 196.00, 246.94, 293.66],  # C, E, G, B, D (Cmaj9)
        [110.00, 130.81, 164.81, 196.00, 261.63],  # A, C, E, G, C (Am7)
        [87.31, 130.81, 174.61, 220.00, 261.63],   # F, C, F, A, C (Fmaj7)
        [98.00, 146.83, 196.00, 220.00, 293.66],   # G, D, G, A, D (Gsus2/4)
    ]
    chord_len = duration_sec / len(chords)
    
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        chord_idx = min(int(t / chord_len), len(chords) - 1)
        chord_t = t % chord_len
        current_chord = chords[chord_idx]
        
        # Envelope for each chord transition (smooth cross-fade)
        attack = 1.2
        release = 1.0
        env = 1.0
        if chord_t < attack:
            env = chord_t / attack
        elif chord_t > (chord_len - release):
            env = max(0.0, (chord_len - chord_t) / release)
            
        # Global fade-in and fade-out
        global_env = 1.0
        if t < 2.0:
            global_env = t / 2.0
        elif t > (duration_sec - 3.0):
            global_env = max(0.0, (duration_sec - t) / 3.0)
            
        val = 0.0
        for f in current_chord:
            # Fundamental + soft second harmonic + subtle chorus detune
            val += 0.35 * math.sin(2 * math.pi * f * t)
            val += 0.15 * math.sin(2 * math.pi * (f * 1.002) * t)
            val += 0.10 * math.sin(2 * math.pi * (f * 0.998) * t)
            val += 0.08 * math.sin(2 * math.pi * (f * 2.0) * t)
            
        # Add subtle warm sub bass
        sub_bass = 0.18 * math.sin(2 * math.pi * (current_chord[0] / 2.0) * t)
        
        sample_val = (val * env * global_env * 0.22) + (sub_bass * env * global_env * 0.15)
        # Soft clip
        sample_val = max(-0.95, min(0.95, sample_val))
        int_sample = int(sample_val * 32767)
        samples.append(int_sample)
        
    with wave.open(output_path, "w") as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Interleave stereo channels
        stereo_data = bytearray()
        for s in samples:
            stereo_data.extend(struct.pack("<hh", s, s))
        wav_file.writeframes(stereo_data)
        
    print(f"Generated ambient soundtrack: {output_path} ({duration_sec}s)")
    return output_path

def generate_sample_images():
    """
    Generate 6 photorealistic stylized real estate demo graphics (1920x1080)
    with clean architectural geometry, lighting, and clear labels.
    """
    rooms = [
        {
            "filename": "1_exterior_facade.jpg",
            "title": "ARCHITECTURAL FAÇADE",
            "subtitle": "Contemporary architecture with manicured landscaped lawns",
            "bg_colors": [(20, 35, 60), (45, 80, 120), (160, 200, 230)],
            "accent": (212, 175, 55),
            "elements": "exterior"
        },
        {
            "filename": "2_living_room.jpg",
            "title": "EXPANSIVE LIVING ROOM",
            "subtitle": "Sun-drenched interiors with hardwood flooring & panoramic windows",
            "bg_colors": [(40, 32, 28), (95, 78, 65), (210, 195, 180)],
            "accent": (212, 175, 55),
            "elements": "living"
        },
        {
            "filename": "3_modular_kitchen.jpg",
            "title": "GOURMET MODULAR KITCHEN",
            "subtitle": "Quartz countertops, Italian cabinetry & premium built-in fittings",
            "bg_colors": [(25, 28, 35), (60, 70, 85), (180, 190, 205)],
            "accent": (220, 160, 40),
            "elements": "kitchen"
        },
        {
            "filename": "4_master_bedroom.jpg",
            "title": "SERENE MASTER BEDROOM",
            "subtitle": "Spacious suite with floor-to-ceiling glass & ambient illumination",
            "bg_colors": [(35, 28, 38), (80, 65, 85), (200, 185, 205)],
            "accent": (212, 175, 55),
            "elements": "bedroom"
        },
        {
            "filename": "5_private_balcony.jpg",
            "title": "PRIVATE BALCONY DECK",
            "subtitle": "Unobstructed sunrise views overlooking verdant city parkland",
            "bg_colors": [(25, 45, 35), (60, 95, 75), (170, 210, 185)],
            "accent": (144, 238, 144),
            "elements": "balcony"
        },
        {
            "filename": "6_covered_parking.jpg",
            "title": "SECURE COVERED PARKING",
            "subtitle": "Dedicated reserved bay with EV charging infrastructure",
            "bg_colors": [(30, 32, 36), (65, 70, 78), (160, 170, 180)],
            "accent": (100, 200, 255),
            "elements": "parking"
        }
    ]
    
    generated_files = []
    width, height = 1920, 1080
    
    for r in rooms:
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)
        
        # Gradient background
        c1, c2, c3 = r["bg_colors"]
        for y in range(height):
            ratio = y / height
            if ratio < 0.5:
                sub_r = ratio / 0.5
                r_val = int(c1[0] * (1 - sub_r) + c2[0] * sub_r)
                g_val = int(c1[1] * (1 - sub_r) + c2[1] * sub_r)
                b_val = int(c1[2] * (1 - sub_r) + c2[2] * sub_r)
            else:
                sub_r = (ratio - 0.5) / 0.5
                r_val = int(c2[0] * (1 - sub_r) + c3[0] * sub_r)
                g_val = int(c2[1] * (1 - sub_r) + c3[1] * sub_r)
                b_val = int(c2[2] * (1 - sub_r) + c3[2] * sub_r)
            draw.line([(0, y), (width, y)], fill=(r_val, g_val, b_val))
            
        # Draw architectural geometry based on room type
        draw_architectural_scene(draw, width, height, r["elements"], r["accent"])
        
        # Overlay stylish semi-transparent badge & info card
        card_w, card_h = 750, 220
        card_x = (width - card_w) // 2
        card_y = height - card_h - 70
        
        # Overlay card box with rounded look
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            fill=(15, 23, 42, 215),
            outline=r["accent"],
            width=2
        )
        
        # Luxury gold tag
        tag_w, tag_h = 240, 36
        tag_x = card_x + (card_w - tag_w) // 2
        tag_y = card_y + 24
        overlay_draw.rectangle(
            [tag_x, tag_y, tag_x + tag_w, tag_y + tag_h],
            fill=r["accent"]
        )
        overlay_draw.text((tag_x + 16, tag_y + 8), "GREENVIEW RESIDENCY", fill=(15, 23, 42))
        
        # Title & Subtitle text
        overlay_draw.text((card_x + 40, card_y + 80), r["title"], fill=(255, 255, 255))
        overlay_draw.text((card_x + 40, card_y + 130), r["subtitle"], fill=(203, 213, 225))
        overlay_draw.text((card_x + 40, card_y + 175), "MOHALI, PUNJAB • ₹85 LAKH • 2-BHK APARTMENT", fill=r["accent"])
        
        # Composite overlay
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        
        out_path = os.path.join(SAMPLE_IMG_DIR, r["filename"])
        img.save(out_path, quality=95)
        generated_files.append(out_path)
        print(f"Generated sample image: {out_path}")
        
    return generated_files

def draw_architectural_scene(draw, w, h, scene_type, accent):
    """Draw pleasant architectural geometry elements representing the space."""
    # Horizon / room perspective lines
    floor_y = int(h * 0.72)
    ceiling_y = int(h * 0.18)
    
    # Perspective wall corners
    draw.line([(0, 0), (int(w * 0.2), ceiling_y)], fill=(120, 130, 145), width=2)
    draw.line([(w, 0), (int(w * 0.8), ceiling_y)], fill=(120, 130, 145), width=2)
    draw.line([(0, h), (int(w * 0.2), floor_y)], fill=(120, 130, 145), width=2)
    draw.line([(w, h), (int(w * 0.8), floor_y)], fill=(120, 130, 145), width=2)
    
    # Back wall boundary
    draw.rectangle([int(w * 0.2), ceiling_y, int(w * 0.8), floor_y], outline=(150, 160, 175), width=2)
    
    # Floor grid / tiles
    for i in range(1, 9):
        fx = int(w * 0.2 + (w * 0.6) * (i / 9))
        draw.line([(fx, floor_y), (int(w * (i / 9)), h)], fill=(100, 110, 125), width=1)
        
    if scene_type == "exterior":
        # Building silhouette with modern window patterns
        draw.rectangle([int(w * 0.3), int(h * 0.22), int(w * 0.7), floor_y], fill=(30, 45, 70), outline=accent, width=3)
        for r_row in range(5):
            for c_col in range(6):
                wx = int(w * 0.33 + c_col * 70)
                wy = int(h * 0.26 + r_row * 65)
                draw.rectangle([wx, wy, wx + 45, wy + 40], fill=(255, 235, 180, 200), outline=(20, 25, 35), width=1)
        # Landscaped lawn
        draw.rectangle([0, floor_y, w, h], fill=(34, 75, 45))
        draw.ellipse([int(w * 0.1), int(h * 0.65), int(w * 0.25), int(h * 0.85)], fill=(40, 95, 55))
        draw.ellipse([int(w * 0.75), int(h * 0.65), int(w * 0.9), int(h * 0.85)], fill=(40, 95, 55))
        
    elif scene_type == "living":
        # Large panoramic window
        draw.rectangle([int(w * 0.28), int(h * 0.25), int(w * 0.72), int(h * 0.68)], fill=(180, 215, 245), outline=(220, 220, 220), width=4)
        # Window mullions
        draw.line([int(w * 0.5), int(h * 0.25), int(w * 0.5), int(h * 0.68)], fill=(150, 150, 150), width=3)
        draw.line([int(w * 0.28), int(h * 0.46), int(w * 0.72), int(h * 0.46)], fill=(150, 150, 150), width=3)
        # Sofa silhouette
        draw.rounded_rectangle([int(w * 0.35), int(h * 0.62), int(w * 0.65), int(h * 0.78)], radius=15, fill=(60, 50, 45), outline=accent, width=2)
        
    elif scene_type == "kitchen":
        # Kitchen island & sleek upper cabinets
        draw.rectangle([int(w * 0.22), int(h * 0.22), int(w * 0.78), int(h * 0.38)], fill=(45, 52, 65), outline=(90, 100, 115), width=2)
        draw.rectangle([int(w * 0.32), int(h * 0.55), int(w * 0.68), int(h * 0.74)], fill=(225, 228, 232), outline=accent, width=3)
        # Pendant lights
        for px in [int(w * 0.4), int(w * 0.5), int(w * 0.6)]:
            draw.line([(px, ceiling_y), (px, int(h * 0.42))], fill=(200, 200, 200), width=2)
            draw.ellipse([px - 14, int(h * 0.42), px + 14, int(h * 0.46)], fill=accent)
            
    elif scene_type == "bedroom":
        # Headboard & king bed
        draw.rounded_rectangle([int(w * 0.32), int(h * 0.48), int(w * 0.68), int(h * 0.76)], radius=12, fill=(65, 50, 68), outline=accent, width=2)
        draw.rectangle([int(w * 0.36), int(h * 0.56), int(w * 0.64), int(h * 0.76)], fill=(235, 230, 238))
        # Warm bedside lamps
        draw.ellipse([int(w * 0.26), int(h * 0.50), int(w * 0.30), int(h * 0.55)], fill=(255, 220, 150))
        draw.ellipse([int(w * 0.70), int(h * 0.50), int(w * 0.74), int(h * 0.55)], fill=(255, 220, 150))
        
    elif scene_type == "balcony":
        # Balcony glass railing & outdoor horizon
        draw.rectangle([int(w * 0.2), int(h * 0.58), int(w * 0.8), int(h * 0.74)], fill=(180, 230, 215, 120), outline=(220, 240, 230), width=3)
        draw.line([int(w * 0.2), int(h * 0.58), int(w * 0.8), int(h * 0.58)], fill=accent, width=4)
        for rx in range(int(w * 0.25), int(w * 0.8), 70):
            draw.line([(rx, int(h * 0.58)), (rx, int(h * 0.74))], fill=(150, 180, 170), width=2)
            
    elif scene_type == "parking":
        # Parking bay markers & ceiling lighting
        draw.rectangle([int(w * 0.3), int(h * 0.58), int(w * 0.7), int(h * 0.78)], outline=(255, 215, 0), width=4)
        draw.text((int(w * 0.45), int(h * 0.63)), "RESERVED - BAY 2B", fill=(255, 215, 0))
        # EV Charger pillar
        draw.rectangle([int(w * 0.22), int(h * 0.45), int(w * 0.28), int(h * 0.74)], fill=(25, 80, 120), outline=(100, 200, 255), width=2)
        draw.text((int(w * 0.23), int(h * 0.48)), "EV FAST\nCHARGER", fill=(255, 255, 255))

if __name__ == "__main__":
    create_ambient_track()
    generate_sample_images()
