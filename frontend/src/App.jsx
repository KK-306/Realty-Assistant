import React, { useState, useEffect } from 'react';
import './App.css';
import LandingScreen from './components/LandingScreen';
import PropertyForm from './components/PropertyForm';
import StoryboardPreview from './components/StoryboardPreview';
import VideoGenerating from './components/VideoGenerating';
import VideoComplete from './components/VideoComplete';
import MyVideosModal from './components/MyVideosModal';
import { Video, Home, RotateCcw, Film, Sparkles, Layers, ArrowRight } from 'lucide-react';
import { apiFetch, apiUrl } from './lib/api';

export default function App() {
  // Wizard Step: 0 = Landing, 1 = Form, 2 = Storyboard, 3 = Generating, 4 = Complete
  const [step, setStep] = useState(0);

  // My Videos modal state
  const [isMyVideosOpen, setIsMyVideosOpen] = useState(false);

  // Shared Application State
  const [formData, setFormData] = useState({
    property_name: '',
    location: '',
    price: '',
    currency: '₹',
    price_display: '',
    property_type: 'apartment',
    key_features: [],
    bedrooms: '2',
    bathrooms: '2',
    description: '',
    script_text: '',
    contact_name: 'Sales Team',
    contact_details: '',
    cta_text: 'Schedule a Visit',
    duration: 30,
    aspect_ratio: '16:9',
    theme: 'luxury',
    voice_accent: 'en-US-BrianNeural',
    narration_enabled: true,
    music_enabled: true,
    image_ids: [],
  });

  const [uploadedImages, setUploadedImages] = useState([]);
  const [storyboard, setStoryboard] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [videoData, setVideoData] = useState(null);
  const [isLoadingSample, setIsLoadingSample] = useState(false);
  const [isStartingRender, setIsStartingRender] = useState(false);
  const [globalError, setGlobalError] = useState('');

  // Step names for wizard breadcrumb
  const stepsList = [
    { num: 1, label: 'Property Details' },
    { num: 2, label: 'AI Storyboard' },
    { num: 3, label: 'Video Rendering' },
    { num: 4, label: 'Export & Share' },
  ];

  // Handler: Load Sample Data from GET /api/samples/listing
  const handleLoadSample = async () => {
    setIsLoadingSample(true);
    setGlobalError('');

    try {
      const res = await apiFetch('/api/samples/listing');
      if (!res.ok) {
        throw new Error(`Failed to load sample listing (HTTP ${res.status})`);
      }

      const sample = await res.json();

      setFormData({
        property_name: sample.property_name || 'Greenview Residency',
        location: sample.location || 'Sector 82, Mohali, Punjab',
        price: sample.price ? String(sample.price) : '8500000',
        currency: sample.currency || '₹',
        price_display: sample.price_display || '₹85 Lakh',
        property_type: sample.property_type || 'apartment',
        key_features: sample.key_features || [
          'Modular Italian Kitchen',
          'Spacious Balcony with Parkland View',
          'Reserved Covered Parking',
          'Abundant Natural Daylight',
        ],
        bedrooms: sample.bedrooms !== undefined ? String(sample.bedrooms) : '2',
        bathrooms: sample.bathrooms !== undefined ? String(sample.bathrooms) : '2',
        description:
          sample.description ||
          'Exquisite 2-BHK luxury apartment featuring contemporary styling, modular fittings, panoramic parkland views, and dedicated covered parking in prime Mohali.',
        contact_name: sample.contact_name || 'Apex Prime Realty',
        contact_details: sample.contact_details || '+91 98765 43210 | apex@realtydemo.com',
        cta_text: sample.cta_text || 'Schedule a Private Viewing',
        duration: sample.duration || 30,
        aspect_ratio: sample.aspect_ratio || '16:9',
        theme: sample.theme || 'luxury',
        voice_accent: sample.voice_accent || 'en-US-BrianNeural',
        narration_enabled: sample.narration_enabled !== undefined ? sample.narration_enabled : true,
        music_enabled: sample.music_enabled !== undefined ? sample.music_enabled : true,
        image_ids: sample.image_ids || [],
      });

      // Prepare sample image objects for uploadedImages state
      if (sample.images && Array.isArray(sample.images)) {
        const mapped = sample.images.map((img) => ({
          image_id: img.image_id,
          filename: img.filename,
          original_filename: img.original_filename || img.filename,
          size_bytes: img.size_bytes || 250000,
          // Serve demo previews from the frontend's static assets so they work
          // even when Render routes API and frontend traffic through different services.
          preview_url: `/sample-properties/${encodeURIComponent(img.filename || img.image_id)}`,
          status: 'success',
        }));
        setUploadedImages(mapped);
      }

      // Advance directly to step 1 (form) so user can inspect and tweak
      setStep(1);
    } catch (err) {
      setGlobalError(err.message || 'Could not fetch sample listing.');
    } finally {
      setIsLoadingSample(false);
    }
  };

  // Handler: When PropertyForm completes validation & storyboard generation
  const handleStoryboardReady = (newStoryboard, newFormData, validImages) => {
    setStoryboard(newStoryboard);
    setFormData(newFormData);
    if (validImages) {
      setUploadedImages(validImages);
    }
    setStep(2); // Move to Storyboard preview
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handler: From StoryboardPreview -> start video generation job
  const handleGenerateVideo = async () => {
    setIsStartingRender(true);
    setGlobalError('');

    try {
      const payload = {
        ...formData,
        price: parseFloat(formData.price),
        duration: parseInt(formData.duration, 10),
        bedrooms: formData.bedrooms !== '' && formData.bedrooms !== undefined ? parseInt(formData.bedrooms, 10) : undefined,
        bathrooms: formData.bathrooms !== '' && formData.bathrooms !== undefined ? parseInt(formData.bathrooms, 10) : undefined,
        image_ids: uploadedImages.map((img) => img.image_id),
      };

      const res = await apiFetch('/api/videos/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...payload, storyboard_preview: storyboard }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to submit video generation job');
      }

      const jobData = await res.json();
      setJobId(jobData.job_id);
      setStep(3); // Move to Video Generating screen
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setGlobalError(err.message || 'Error initiating video render.');
    } finally {
      setIsStartingRender(false);
    }
  };

  // Handler: When generation is completed
  const handleVideoReady = (completedJob) => {
    setVideoData(completedJob);
    setStep(4); // Move to Complete screen
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Save video into localStorage for "My Videos"
    try {
      const existing = JSON.parse(localStorage.getItem('ra_property_studio_videos') || '[]');
      const newEntry = {
        video_id: completedJob.video_id || completedJob.job_id,
        property_name: formData.property_name || 'Promotional Property Video',
        location: formData.location || 'Prime Real Estate',
        duration: completedJob.metadata?.duration_seconds || formData.duration || 30,
        aspect_ratio: completedJob.metadata?.aspect_ratio || formData.aspect_ratio || '16:9',
        stream_url: apiUrl(`/api/videos/${completedJob.video_id || completedJob.job_id}/stream`),
        download_url: apiUrl(completedJob.download_url || `/api/videos/${completedJob.video_id}/download`),
        date: new Date().toISOString(),
      };
      // Keep most recent first, limit to 20
      const filtered = existing.filter((item) => item.video_id !== newEntry.video_id);
      localStorage.setItem('ra_property_studio_videos', JSON.stringify([newEntry, ...filtered].slice(0, 20)));
    } catch {
      // Storage unavailable or disabled
    }
  };

  // Handler: Reset everything to landing
  const handleReset = () => {
    setStep(0);
    setStoryboard(null);
    setJobId(null);
    setVideoData(null);
    setGlobalError('');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Navigation handlers
  const handleNavigateHome = () => {
    setStep(0);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigateCreate = () => {
    setStep(1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigateHowItWorks = () => {
    if (step !== 0) {
      setStep(0);
      setTimeout(() => {
        const el = document.getElementById('how-it-works');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } else {
      const el = document.getElementById('how-it-works');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F7FC] text-[#292943] flex flex-col font-sans selection:bg-[#344E8B] selection:text-white">
      {/* ------------------------------------------------------------- */}
      {/* TOP BRAND NAVIGATION BAR (BLUE-MAGENTA GRADIENT)               */}
      {/* ------------------------------------------------------------- */}
      <header className="sticky top-0 z-40 bg-gradient-to-r from-[#344E8B] via-[#67417F] to-[#A93478] text-white shadow-md px-4 sm:px-6 lg:px-8 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          
          {/* Brand Wordmark & Logo */}
          <div
            onClick={handleNavigateHome}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="bg-white px-2 py-1 rounded-xl shadow-sm border border-white/20 group-hover:scale-105 transition-transform flex items-center">
              <img
                src="/realty-assistant-logo.png"
                alt="Realty Assistant"
                className="h-7 w-auto object-contain"
              />
            </div>
            <div>
              <div className="text-base sm:text-lg font-extrabold font-outfit tracking-tight text-white flex items-center gap-1.5 leading-none">
                <span>RA Property Studio</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-white text-[#344E8B] font-bold tracking-normal uppercase">
                  AI
                </span>
              </div>
              <div className="text-[10px] uppercase tracking-wider text-white/80 font-medium mt-1">
                Part of Viraj Ventures
              </div>
            </div>
          </div>

          {/* Stepper (Visible for step >= 1 on desktop) */}
          {step > 0 && (
            <div className="hidden lg:flex items-center gap-2">
              {stepsList.map((st, idx) => {
                const isActive = step === st.num;
                const isPassed = step > st.num;

                return (
                  <React.Fragment key={st.num}>
                    <div
                      className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                        isActive
                          ? 'bg-white text-[#344E8B] shadow-sm font-bold'
                          : isPassed
                          ? 'text-white/90 bg-white/20'
                          : 'text-white/60 bg-black/15'
                      }`}
                    >
                      <span className="w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold bg-white/20">
                        {isPassed ? '✓' : st.num}
                      </span>
                      <span>{st.label}</span>
                    </div>

                    {idx < stepsList.length - 1 && (
                      <span className="text-white/40 text-xs">/</span>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          )}

          {/* Right Navigation Links & Actions */}
          <nav className="flex items-center gap-1 sm:gap-3 text-xs sm:text-sm font-semibold">
            {step === 0 && (
              <>
                <button
                  type="button"
                  onClick={handleNavigateHome}
                  className="px-2.5 py-1.5 rounded-lg text-white/90 hover:text-white hover:bg-white/10 transition-colors cursor-pointer hidden md:inline-block"
                >
                  Home
                </button>
                <button
                  type="button"
                  onClick={handleNavigateHowItWorks}
                  className="px-2.5 py-1.5 rounded-lg text-white/90 hover:text-white hover:bg-white/10 transition-colors cursor-pointer hidden md:inline-block"
                >
                  How It Works
                </button>
              </>
            )}

            {/* My Videos Button (Always functional) */}
            <button
              type="button"
              onClick={() => setIsMyVideosOpen(true)}
              className="px-3 py-1.5 rounded-lg text-white hover:bg-white/15 border border-white/25 transition-colors flex items-center gap-1.5 cursor-pointer text-xs sm:text-sm"
              title="View your generated videos"
            >
              <Film className="w-3.5 h-3.5" />
              <span>My Videos</span>
            </button>

            {/* Primary Action Button */}
            {step === 0 ? (
              <button
                type="button"
                onClick={handleNavigateCreate}
                className="bg-white text-[#344E8B] hover:bg-slate-100 font-bold px-3.5 py-1.5 rounded-lg text-xs sm:text-sm flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
              >
                <Video className="w-3.5 h-3.5 text-[#344E8B]" />
                <span>Create Video</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleReset}
                className="px-3 py-1.5 rounded-lg bg-white/15 hover:bg-white/25 text-white text-xs flex items-center gap-1.5 transition-colors cursor-pointer"
                title="Restart workflow"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Reset</span>
              </button>
            )}
          </nav>
        </div>
      </header>

      {/* Global Error Banner */}
      {globalError && (
        <div className="bg-[#C53C53] text-white py-2.5 px-4 text-center text-xs sm:text-sm font-medium shadow-sm">
          <span>{globalError}</span>
        </div>
      )}

      {/* Main Content Area: Step Router */}
      <main className="flex-1">
        {step === 0 && (
          <LandingScreen
            onStart={() => {
              setStep(1);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            onLoadSample={handleLoadSample}
            isLoadingSample={isLoadingSample}
            onExploreHowItWorks={handleNavigateHowItWorks}
          />
        )}

        {step === 1 && (
          <PropertyForm
            initialData={formData}
            uploadedImages={uploadedImages}
            onStoryboardReady={handleStoryboardReady}
            onBack={() => {
              setStep(0);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
          />
        )}

        {step === 2 && (
          <StoryboardPreview
            storyboard={storyboard}
            formData={formData}
            uploadedImages={uploadedImages}
            onGenerateVideo={handleGenerateVideo}
            onStoryboardChange={setStoryboard}
            onBackToEdit={() => {
              setStep(1);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            isGenerating={isStartingRender}
          />
        )}

        {step === 3 && (
          <VideoGenerating
            jobId={jobId}
            onVideoReady={handleVideoReady}
            onRetry={handleGenerateVideo}
            onBackToEdit={() => {
              setStep(1);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
          />
        )}

        {step === 4 && (
          <VideoComplete
            videoJob={videoData}
            formData={formData}
            onReset={handleReset}
            onRegenerate={() => {
              setStep(2);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
          />
        )}
      </main>

      {/* My Videos Modal Dialog */}
      <MyVideosModal
        isOpen={isMyVideosOpen}
        onClose={() => setIsMyVideosOpen(false)}
        onCreateNew={() => {
          setIsMyVideosOpen(false);
          setStep(1);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        onLoadSample={() => {
          setIsMyVideosOpen(false);
          handleLoadSample();
        }}
      />

      {/* ------------------------------------------------------------- */}
      {/* BRAND FOOTER                                                  */}
      {/* ------------------------------------------------------------- */}
      <footer className="border-t border-[#E5E5EF] bg-white py-8 px-4 text-xs text-[#686A7D] mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-3 text-center sm:text-left">
            <span className="font-bold text-[#292943] font-outfit text-sm">
              RA Property Studio AI
            </span>
            <span className="hidden sm:inline text-slate-300">•</span>
            <span className="text-[#686A7D]">
              Every Property. A Story Worth Sharing.
            </span>
          </div>

          <div className="flex items-center gap-4 text-[#686A7D] text-xs">
            <span>Realty Assistant</span>
            <span>•</span>
            <span>Viraj Ventures</span>
            <span>•</span>
            <span>H.264 / AAC Full HD MP4</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
