import React, { useState } from 'react';
import {
  Play,
  Clock,
  Type,
  Film,
  ChevronDown,
  ChevronUp,
  Eye,
  Volume2,
  Sparkles,
  ArrowLeft,
  Layers,
  CheckCircle2,
  Monitor,
  Palette,
  Pencil,
  Check
} from 'lucide-react';

export default function StoryboardPreview({
  storyboard,
  formData,
  uploadedImages,
  onGenerateVideo,
  onBackToEdit,
  isGenerating,
  onStoryboardChange,
}) {
  const [showFullScript, setShowFullScript] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  if (!storyboard || !storyboard.scenes) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 text-center">
        <p className="text-[#686A7D]">No storyboard generated yet.</p>
        <button
          onClick={onBackToEdit}
          className="mt-4 px-4 py-2 rounded-lg brand-gradient-btn text-white text-sm"
        >
          Return to Form
        </button>
      </div>
    );
  }

  const { script, scenes, total_duration, aspect_ratio, theme } = storyboard;

  const updateStoryboard = (update) => {
    if (!onStoryboardChange) return;

    onStoryboardChange((current) => {
      if (!current) return current;

      const next = update(current);
      const sceneVoiceovers = next.scenes.map((scene) => scene.voiceover_text || '');
      return {
        ...next,
        script: {
          ...next.script,
          scene_voiceovers: sceneVoiceovers,
          voiceover_full: sceneVoiceovers.filter(Boolean).join(' '),
        },
      };
    });
  };

  const updateScript = (field, value) => {
    updateStoryboard((current) => ({
      ...current,
      script: { ...current.script, [field]: value },
      // The opening hook and closing CTA are spoken in the first and last scenes.
      scenes: current.scenes.map((scene, index) => {
        if (field === 'opening_hook' && index === 0) {
          return { ...scene, voiceover_text: value };
        }
        if (field === 'closing_cta' && index === current.scenes.length - 1) {
          return { ...scene, voiceover_text: value };
        }
        return scene;
      }),
    }));
  };

  const updateScene = (sceneIndex, field, value) => {
    updateStoryboard((current) => {
      const scenes = current.scenes.map((scene, index) => {
        if (index !== sceneIndex) return scene;
        if (field.startsWith('overlay.')) {
          const overlayField = field.slice('overlay.'.length);
          return {
            ...scene,
            overlay: { ...scene.overlay, [overlayField]: value },
          };
        }
        return { ...scene, [field]: value };
      });

      return {
        ...current,
        scenes,
        ...(field === 'voiceover_text' && sceneIndex === scenes.length - 1
          ? { script: { ...current.script, closing_cta: value } }
          : {}),
      };
    });
  };

  const inputClassName = 'w-full rounded-lg border border-[#D9D9E6] bg-white px-3 py-2 text-sm text-[#292943] outline-none focus:border-[#344E8B] focus:ring-2 focus:ring-[#344E8B]/10';
  const textareaClassName = `${inputClassName} resize-y`;

  // Scene Type badge styling helper
  const getSceneTypeBadge = (type) => {
    switch (type) {
      case 'opening':
        return {
          label: 'Opening Hook',
          classes: 'bg-[#344E8B]/10 border-[#344E8B]/30 text-[#344E8B]',
        };
      case 'feature':
        return {
          label: 'Feature Showcase',
          classes: 'bg-[#67417F]/10 border-[#67417F]/30 text-[#67417F]',
        };
      case 'highlight':
        return {
          label: 'Prime Highlight',
          classes: 'bg-[#A93478]/10 border-[#A93478]/30 text-[#A93478]',
        };
      case 'closing':
        return {
          label: 'Closing & CTA',
          classes: 'bg-[#21865B]/10 border-[#21865B]/30 text-[#21865B]',
        };
      default:
        return {
          label: type,
          classes: 'bg-slate-100 border-slate-300 text-slate-700',
        };
    }
  };

  // Find image preview for a given image_id
  const getSceneImage = (imageId, index) => {
    const found = uploadedImages?.find((img) => img.image_id === imageId);
    if (found?.preview_url) return found.preview_url;
    if (uploadedImages?.[index]?.preview_url) return uploadedImages[index].preview_url;
    return `/api/images/${imageId}/preview`;
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8 animate-fade-in">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 pb-4 border-b border-[#E5E5EF]">
        <button
          type="button"
          onClick={onBackToEdit}
          className="inline-flex items-center gap-2 text-sm text-[#686A7D] hover:text-[#292943] transition-colors cursor-pointer w-fit"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Edit Listing</span>
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs uppercase font-bold tracking-wider text-[#344E8B]">Step 2 of 3</span>
          <span className="text-slate-300">•</span>
          <span className="text-xs font-semibold text-[#686A7D]">Storyboard Approval</span>
          <button
            type="button"
            onClick={() => setIsEditing((editing) => !editing)}
            className="ml-2 inline-flex items-center gap-1.5 rounded-lg border border-[#344E8B]/30 bg-white px-3 py-2 text-xs font-semibold text-[#344E8B] transition-colors hover:bg-[#344E8B]/5"
          >
            {isEditing ? <Check className="h-3.5 w-3.5" /> : <Pencil className="h-3.5 w-3.5" />}
            {isEditing ? 'Done editing' : 'Edit storyboard'}
          </button>
        </div>
      </div>

      {/* Hero Title & Badges */}
      <div className="brand-card p-6 sm:p-8 mb-8 bg-white border border-[#E5E5EF] shadow-sm relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="px-3 py-1 rounded-full bg-[#344E8B]/10 border border-[#344E8B]/30 text-[#344E8B] text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                AI Storyboard Ready
              </span>
              <span className="px-3 py-1 rounded-full bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] text-xs font-semibold flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[#344E8B]" />
                {total_duration} Seconds Total
              </span>
              <span className="px-3 py-1 rounded-full bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] text-xs font-semibold flex items-center gap-1.5">
                <Monitor className="w-3.5 h-3.5 text-[#67417F]" />
                {aspect_ratio} Format
              </span>
              <span className="px-3 py-1 rounded-full bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] text-xs font-semibold uppercase flex items-center gap-1.5">
                <Palette className="w-3.5 h-3.5 text-[#A93478]" />
                {theme}
              </span>
            </div>

            {isEditing ? (
              <label className="block">
                <span className="mb-1 block text-xs font-semibold text-[#686A7D]">Video title</span>
                <input
                  value={script?.video_title || ''}
                  onChange={(event) => updateScript('video_title', event.target.value)}
                  className={`${inputClassName} text-xl font-bold sm:text-2xl`}
                />
              </label>
            ) : (
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold font-outfit text-[#292943] leading-tight">
                {script?.video_title || formData?.property_name || 'Cinematic Property Showcase'}
              </h1>
            )}

            {/* Opening Hook Banner */}
            {(script?.opening_hook || isEditing) && (
              <div className="mt-4 p-4 rounded-xl bg-gradient-to-r from-[#344E8B]/5 to-[#A93478]/5 border border-[#344E8B]/20 text-[#292943] text-sm leading-relaxed">
                <span className="font-bold text-[#344E8B] uppercase text-xs tracking-wider block mb-1">
                  Opening Hook {isEditing ? '(spoken narration)' : ''}:
                </span>
                {isEditing ? (
                  <textarea
                    rows={3}
                    value={script?.opening_hook || ''}
                    onChange={(event) => updateScript('opening_hook', event.target.value)}
                    className={textareaClassName}
                  />
                ) : `"${script.opening_hook}"`}
              </div>
            )}
          </div>

          {/* Action CTA Box */}
          <div className="flex flex-col sm:flex-row lg:flex-col gap-3 shrink-0 lg:w-64">
            <button
              onClick={onGenerateVideo}
              disabled={isGenerating}
              className="brand-gradient-btn px-6 py-4 rounded-xl text-white font-bold text-base flex items-center justify-center gap-2.5 shadow-lg cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isGenerating ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Starting Engine...</span>
                </>
              ) : (
                <>
                  <Play className="w-5 h-5 fill-white text-white" />
                  <span>Generate Video</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={onBackToEdit}
              className="px-5 py-3 rounded-xl border border-[#E5E5EF] bg-white text-[#686A7D] hover:text-[#292943] hover:border-[#344E8B] text-sm font-semibold transition-colors cursor-pointer text-center"
            >
              Back to Edit
            </button>
          </div>
        </div>
      </div>

      {/* Voiceover Accordion */}
      {script?.voiceover_full && (
        <div className="brand-card rounded-2xl mb-8 overflow-hidden bg-white border border-[#E5E5EF] shadow-sm">
          <button
            type="button"
            onClick={() => setShowFullScript(!showFullScript)}
            className="w-full p-5 sm:px-6 flex items-center justify-between text-left hover:bg-[#F7F7FC] transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#344E8B]/10 border border-[#344E8B]/20 flex items-center justify-center text-[#344E8B]">
                <Volume2 className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#292943] font-outfit">Full Voiceover Script</h4>
                <p className="text-xs text-[#686A7D]">Click to view complete spoken narration</p>
              </div>
            </div>
            <div className="text-[#686A7D]">
              {showFullScript ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </div>
          </button>

          {showFullScript && (
            <div className="px-6 pb-6 pt-2 border-t border-[#E5E5EF] text-sm text-[#292943] leading-relaxed space-y-3 bg-[#F7F7FC]">
              <p className="italic bg-white p-4 rounded-xl border border-[#E5E5EF]">
                "{script.voiceover_full}"
              </p>
              {(script.closing_cta || isEditing) && (
                <div className="text-xs text-[#A93478] font-bold">
                  {isEditing ? (
                    <label className="block">
                      <span className="mb-1 block">Closing Call (updates the final scene narration)</span>
                      <textarea
                        rows={2}
                        value={script.closing_cta}
                        onChange={(event) => updateScript('closing_cta', event.target.value)}
                        className={textareaClassName}
                      />
                    </label>
                  ) : (
                    <><strong>Closing Call:</strong> {script.closing_cta}</>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Scene Timeline Review */}
      <div className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-[#344E8B]" />
            <h3 className="text-lg font-bold font-outfit text-[#292943]">
              Scene Breakdown ({scenes.length} Scenes)
            </h3>
          </div>
          <span className="text-xs text-[#686A7D]">Paced for optimal viewer retention</span>
        </div>

        <div className="space-y-6">
          {scenes.map((scene, idx) => {
            const badge = getSceneTypeBadge(scene.scene_type);
            const imageUrl = getSceneImage(scene.image_id, idx);

            return (
              <div
                key={scene.scene_index ?? idx}
                className="brand-card brand-card-hover rounded-2xl overflow-hidden bg-white border border-[#E5E5EF] shadow-sm transition-all"
              >
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 p-5 sm:p-6">
                  {/* Left Column: Visual Preview */}
                  <div className="md:col-span-4 lg:col-span-4 flex flex-col justify-between">
                    <div className="relative rounded-xl overflow-hidden aspect-video bg-slate-900 border border-[#E5E5EF] group/img">
                      <img
                        src={imageUrl}
                        alt={scene.caption || `Scene ${idx + 1}`}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="%2394a3b8" stroke-width="1"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>';
                        }}
                      />

                      {/* Scene Badge */}
                      <div className="absolute top-2 left-2 bg-white/90 backdrop-blur-md px-2.5 py-1 rounded-md text-xs font-bold text-[#344E8B] border border-[#E5E5EF] shadow-sm">
                        Scene #{idx + 1}
                      </div>

                      {scene.generated_image && (
                        <div className="absolute top-2 right-2 bg-[#A93478]/90 px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide text-white shadow-sm">
                          AI concept image
                        </div>
                      )}

                      {/* Duration Tag */}
                      <div className="absolute bottom-2 right-2 bg-black/75 backdrop-blur-md px-2 py-0.5 rounded text-[11px] font-semibold text-white flex items-center gap-1">
                        <Clock className="w-3 h-3 text-white" />
                        <span>{scene.duration}s</span>
                      </div>

                      {/* View icon badge */}
                      <div className="absolute bottom-2 left-2 p-1 rounded bg-black/70 text-white opacity-0 group-hover/img:opacity-100 transition-opacity">
                        <Eye className="w-3.5 h-3.5" />
                      </div>
                    </div>

                    <div className="mt-3 text-[11px] text-[#686A7D] flex items-center justify-between">
                      <span className="flex items-center gap-1">
                        <Film className="w-3 h-3 text-[#344E8B]" />
                        <span>Img ID: <code className="text-[#292943] font-mono text-[10px]">{scene.image_id.slice(0, 8)}</code></span>
                      </span>
                      <span className="text-[#21865B] font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Ken Burns Ready
                      </span>
                    </div>
                  </div>

                  {/* Right Column: Scene Content & Overlay Info */}
                  <div className="md:col-span-8 lg:col-span-8 flex flex-col justify-between space-y-4">
                    {/* Header tags */}
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${badge.classes}`}>
                        {badge.label}
                      </span>
                      <span className="text-xs text-[#686A7D]">
                        {scene.duration} seconds • Scene {idx + 1} of {scenes.length}
                      </span>
                    </div>

                    {isEditing && (
                      <label className="block">
                        <span className="mb-1 block text-xs font-semibold text-[#686A7D]">Scene caption</span>
                        <input
                          value={scene.caption || ''}
                          onChange={(event) => updateScene(idx, 'caption', event.target.value)}
                          className={inputClassName}
                        />
                      </label>
                    )}

                    {/* Graphic Overlays Box */}
                    <div className="p-4 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF]">
                      <div className="text-[11px] uppercase tracking-wider text-[#344E8B] font-bold mb-2 flex items-center gap-1.5">
                        <Type className="w-3.5 h-3.5" />
                        <span>On-Screen Graphic Overlay</span>
                      </div>

                      {isEditing ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {[
                            ['tag', 'Tag'],
                            ['title', 'Title'],
                            ['subtitle', 'Subtitle'],
                            ['badge', 'Badge'],
                            ['footer', 'Footer'],
                          ].map(([field, label]) => (
                            <label key={field} className={field === 'subtitle' || field === 'footer' ? 'sm:col-span-2' : ''}>
                              <span className="mb-1 block text-[11px] font-semibold text-[#686A7D]">{label}</span>
                              <input
                                value={scene.overlay?.[field] || ''}
                                onChange={(event) => updateScene(idx, `overlay.${field}`, event.target.value)}
                                className={inputClassName}
                              />
                            </label>
                          ))}
                        </div>
                      ) : (
                        <>
                          {scene.overlay?.tag && (
                            <div className="text-[10px] uppercase font-bold text-[#A93478] tracking-wider mb-1">
                              [{scene.overlay.tag}]
                            </div>
                          )}

                          <h4 className="text-base sm:text-lg font-bold font-outfit text-[#292943]">
                            {scene.overlay?.title || scene.caption}
                          </h4>

                          {scene.overlay?.subtitle && (
                            <p className="text-xs text-[#686A7D] mt-1">
                              {scene.overlay.subtitle}
                            </p>
                          )}

                          <div className="flex flex-wrap gap-3 mt-3 pt-2 border-t border-[#E5E5EF] text-xs">
                            {scene.overlay?.badge && (
                              <span className="px-2 py-0.5 rounded bg-[#344E8B]/10 text-[#344E8B] font-semibold">
                                Badge: {scene.overlay.badge}
                              </span>
                            )}
                            {scene.overlay?.footer && (
                              <span className="text-[#686A7D] italic">
                                Footer: {scene.overlay.footer}
                              </span>
                            )}
                          </div>
                        </>
                      )}
                    </div>

                    {/* Voiceover text */}
                    {(scene.voiceover_text || isEditing) && (
                      <div className="flex items-start gap-2.5 text-xs sm:text-sm text-[#292943] bg-white p-3.5 rounded-xl border border-[#E5E5EF]">
                        <Volume2 className="w-4 h-4 text-[#A93478] shrink-0 mt-0.5" />
                        {isEditing && idx > 0 ? (
                          <label className="flex-1">
                            <span className="mb-1 block font-bold text-[#344E8B]">Scene narration</span>
                            <textarea
                              rows={3}
                              value={scene.voiceover_text || ''}
                              onChange={(event) => updateScene(idx, 'voiceover_text', event.target.value)}
                              className={textareaClassName}
                            />
                          </label>
                        ) : isEditing ? (
                          <div>
                            <strong className="text-[#344E8B]">Scene narration:</strong>{' '}
                            <span>The opening scene narration is linked to the opening hook above.</span>
                          </div>
                        ) : (
                          <div>
                            <strong className="text-[#344E8B]">Narration:</strong>{' '}
                            <span className="text-[#292943]">"{scene.voiceover_text}"</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Floating Bottom Action Bar */}
      <div className="sticky bottom-4 z-20 brand-card p-4 sm:p-5 border border-[#344E8B]/30 shadow-xl bg-white flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <div className="text-sm font-bold text-[#292943] font-outfit">Ready to create this property video?</div>
          <div className="text-xs text-[#686A7D]">
            Rendering takes approx. 30-60 seconds depending on duration.
          </div>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button
            type="button"
            onClick={onBackToEdit}
            className="w-full sm:w-auto px-5 py-3 rounded-xl border border-[#E5E5EF] bg-white text-[#686A7D] hover:text-[#292943] hover:border-[#344E8B] text-sm font-semibold transition-colors cursor-pointer"
          >
            Edit Settings
          </button>

          <button
            onClick={onGenerateVideo}
            disabled={isGenerating}
            className="w-full sm:w-auto brand-gradient-btn px-8 py-3 rounded-xl text-white font-bold text-sm sm:text-base flex items-center justify-center gap-2 shadow-lg cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isGenerating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Submitting Job...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white text-white" />
                <span>Start Video Render</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
