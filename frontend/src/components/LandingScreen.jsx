import React, { useState, useEffect, useRef } from 'react';
import {
  Video,
  Sparkles,
  Download,
  ArrowRight,
  Home,
  CheckCircle2,
  Clock,
  Layers,
  FileText,
  Volume2,
  Maximize2,
  Play,
  Pause,
  Film,
  Building,
  Check,
  ChevronRight,
  ShieldCheck,
  Sliders,
  Palette
} from 'lucide-react';

export default function LandingScreen({
  onStart,
  onLoadSample,
  isLoadingSample,
  onExploreHowItWorks
}) {
  const [demoVideoUrl, setDemoVideoUrl] = useState(null);
  const [isPlayingDemo, setIsPlayingDemo] = useState(false);
  const videoRef = useRef(null);

  // Check if a demo video is available from the backend
  useEffect(() => {
    fetch('/api/samples/video')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.available && data?.stream_url) {
          setDemoVideoUrl(data.stream_url);
        }
      })
      .catch(() => {
        // Fallback to static preview
      });
  }, []);

  const handleTogglePlay = () => {
    if (demoVideoUrl && videoRef.current) {
      if (isPlayingDemo) {
        videoRef.current.pause();
        setIsPlayingDemo(false);
      } else {
        videoRef.current.play();
        setIsPlayingDemo(true);
      }
    } else {
      // If no video file is rendered yet, toggle state for interactive visual preview
      setIsPlayingDemo(!isPlayingDemo);
    }
  };

  const handleScrollToHowItWorks = () => {
    if (onExploreHowItWorks) {
      onExploreHowItWorks();
    } else {
      const el = document.getElementById('how-it-works');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  // Benefits below hero buttons
  const heroBenefits = [
    {
      num: '01',
      title: 'Your Photos',
      desc: 'Upload property images.',
      icon: Home,
    },
    {
      num: '02',
      title: 'AI Storytelling',
      desc: 'Generate scripts and captions.',
      icon: Sparkles,
    },
    {
      num: '03',
      title: 'Ready-to-Share',
      desc: 'Preview and download your MP4.',
      icon: Download,
    },
  ];

  // How It Works Steps
  const howItWorksSteps = [
    {
      step: '1',
      title: 'Upload Photos',
      badge: '4 to 8 Images',
      desc: 'Upload high-resolution property exterior and interior photos. Reorder images to establish your desired visual narrative.',
      icon: Home,
      features: ['JPEG, PNG, WebP supported', 'Visual drag-and-drop reordering', 'Automatic format validation'],
    },
    {
      step: '2',
      title: 'Generate Storyboard',
      badge: 'AI Scripting',
      desc: 'Our AI engine drafts factual scene-by-scene narration and overlay captions directly grounded in your verified property details.',
      icon: Sparkles,
      features: ['Factual, grounded claims only', 'Scene timing calculation', 'Customizable luxury themes'],
    },
    {
      step: '3',
      title: 'Export Video',
      badge: 'Studio 1080p MP4',
      desc: 'Render your video with cinematic Ken Burns motion, dynamic lower thirds, synchronized voiceover narration, and ambient lounge audio.',
      icon: Film,
      features: ['16:9 Landscape & 9:16 Vertical', 'H.264 / AAC standard MP4', 'Instant high-speed download'],
    },
  ];

  // Features list
  const featuresList = [
    {
      icon: Sparkles,
      title: 'AI Script Generation',
      desc: 'Creates factual, engaging voiceover scripts and scene headlines tailored strictly to your property features with zero hallucinations.',
    },
    {
      icon: Sliders,
      title: 'Automatic Scene Sequencing',
      desc: 'Smart duration budgeting aligns scene transitions to match your requested duration (20s, 30s, or 40s) seamlessly.',
    },
    {
      icon: FileText,
      title: 'Dynamic Captions & Overlays',
      desc: 'Clean, broadcast-quality typographic overlays highlight key features, pricing, and agent contact details without cluttering photos.',
    },
    {
      icon: Volume2,
      title: 'Natural Voiceover Narration',
      desc: 'Neural voice synthesis speaks your listing highlights clearly, paired with volume-balanced background lounge music.',
    },
    {
      icon: Maximize2,
      title: 'Aspect-Ratio Selection',
      desc: 'Choose 16:9 widescreen for YouTube and property portals, or 9:16 vertical for Instagram Reels, YouTube Shorts, and WhatsApp stories.',
    },
    {
      icon: Download,
      title: 'Instant Studio MP4 Export',
      desc: 'Powered by an industrial-grade FFmpeg rendering pipeline delivering standard H.264 video with AAC audio ready to publish anywhere.',
    },
  ];

  // Demo gallery images
  const sampleThumbnails = [
    { name: '1_exterior_facade.jpg', label: 'Exterior Facade' },
    { name: '2_living_room.jpg', label: 'Living Room' },
    { name: '3_modular_kitchen.jpg', label: 'Modular Kitchen' },
    { name: '4_master_bedroom.jpg', label: 'Master Bedroom' },
    { name: '5_private_balcony.jpg', label: 'Balcony View' },
    { name: '6_covered_parking.jpg', label: 'Reserved Parking' },
  ];

  return (
    <div className="animate-fade-in">
      {/* ------------------------------------------------------------- */}
      {/* HERO SECTION                                                  */}
      {/* ------------------------------------------------------------- */}
      <section className="relative overflow-hidden pt-8 pb-16 lg:pt-14 lg:pb-24 border-b border-[#E5E5EF] bg-gradient-to-b from-[#FFFFFF] to-[#F7F7FC]">
        {/* Subtle Brand Ambient Glow */}
        <div className="absolute top-1/4 right-1/4 w-[450px] h-[350px] bg-gradient-to-tr from-[#344E8B]/10 via-[#67417F]/10 to-[#A93478]/10 rounded-full blur-[100px] pointer-events-none -z-10" />
        <div className="absolute bottom-10 left-10 w-[300px] h-[200px] bg-[#344E8B]/5 rounded-full blur-[90px] pointer-events-none -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            
            {/* Left Column: Headline, Description & CTAs */}
            <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
              {/* Brand Logo & Eyebrow */}
              <div className="flex flex-col sm:flex-row items-center lg:items-start gap-3.5 pt-1">
                <div className="bg-white px-3.5 py-2 rounded-xl border border-[#E5E5EF] shadow-sm inline-flex items-center">
                  <img
                    src="/realty-assistant-logo.png"
                    alt="Realty Assistant Logo"
                    className="h-9 sm:h-10 w-auto object-contain"
                  />
                </div>
                <div className="inline-flex items-center gap-2 px-3.5 py-2 rounded-full bg-white border border-[#E5E5EF] shadow-sm my-auto">
                  <span className="w-2 h-2 rounded-full bg-[#A93478] animate-pulse" />
                  <span className="text-[11px] sm:text-xs font-bold uppercase tracking-wider text-[#344E8B]">
                    SMARTER PROPERTY MARKETING STARTS HERE
                  </span>
                </div>
              </div>

              {/* Main Headline */}
              <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold font-outfit text-[#292943] tracking-tight leading-[1.15]">
                Your Properties Deserve More Than Just Photos.
              </h1>

              {/* Highlighted Supporting Headline */}
              <p className="text-xl sm:text-2xl font-bold font-outfit brand-gradient-text leading-snug">
                Turn Listings Into Stories. Stories Into Opportunities.
              </p>

              {/* Description */}
              <p className="text-base sm:text-lg text-[#686A7D] max-w-2xl mx-auto lg:mx-0 leading-relaxed font-normal">
                Transform your property images and details into cinematic, ready-to-share promotional videos with AI-generated scripts, elegant visuals, and compelling calls to action — all in just a few clicks.
              </p>

              {/* Primary & Secondary CTAs */}
              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-2">
                <button
                  type="button"
                  onClick={onStart}
                  className="brand-gradient-btn px-8 py-4 rounded-xl text-white font-bold text-base flex items-center justify-center gap-3 w-full sm:w-auto shadow-lg cursor-pointer"
                >
                  <Video className="w-5 h-5 text-white" />
                  <span>Create Property Video</span>
                  <ArrowRight className="w-5 h-5 text-white" />
                </button>

                <button
                  type="button"
                  onClick={handleScrollToHowItWorks}
                  className="brand-outline-btn px-7 py-4 rounded-xl text-base flex items-center justify-center gap-2 w-full sm:w-auto cursor-pointer"
                >
                  <span>Explore How It Works</span>
                  <ChevronRight className="w-4 h-4 text-[#344E8B]" />
                </button>
              </div>

              {/* Three Concise Benefits Under Buttons */}
              <div className="pt-6 border-t border-[#E5E5EF] grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
                {heroBenefits.map((b) => {
                  const Icon = b.icon;
                  return (
                    <div key={b.num} className="flex items-start gap-3 p-2.5 rounded-xl bg-white/70 border border-[#E5E5EF]/80">
                      <div className="w-8 h-8 rounded-lg bg-[#344E8B]/10 text-[#344E8B] flex items-center justify-center flex-shrink-0 mt-0.5 font-bold text-xs">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-[#292943]">{b.title}</div>
                        <div className="text-[11px] text-[#686A7D] leading-tight mt-0.5">{b.desc}</div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Brand Attribution */}
              <div className="flex items-center justify-center lg:justify-start gap-2.5 text-xs font-medium text-[#686A7D] pt-1">
                <span>by</span>
                <img
                  src="/realty-assistant-logo.png"
                  alt="Realty Assistant"
                  className="h-5 w-auto object-contain inline-block bg-white px-1.5 py-0.5 rounded border border-[#E5E5EF]"
                />
                <span>| Part of <strong className="text-[#67417F]">Viraj Ventures</strong></span>
              </div>
            </div>

            {/* Right Column: Hero Visual Product Preview Composition */}
            <div className="lg:col-span-5 relative flex justify-center">
              {/* Product Preview Card */}
              <div className="w-full max-w-md brand-card p-4 relative overflow-hidden shadow-2xl border border-[#E5E5EF]">
                
                {/* Visual Header / Tag */}
                <div className="flex items-center justify-between mb-3 px-1">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#21865B] animate-ping" />
                    <span className="text-[11px] font-bold text-[#292943] uppercase tracking-wider">
                      Live Studio Preview
                    </span>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#A93478]/10 text-[#A93478] border border-[#A93478]/20">
                    DEMO LISTING
                  </span>
                </div>

                {/* Main Media Preview Frame */}
                <div className="relative aspect-video rounded-xl overflow-hidden bg-slate-900 border border-slate-200 shadow-md group">
                  {demoVideoUrl ? (
                    <video
                      ref={videoRef}
                      src={demoVideoUrl}
                      playsInline
                      loop
                      className="w-full h-full object-cover"
                      poster="/sample-properties/1_exterior_facade.jpg"
                      onPlay={() => setIsPlayingDemo(true)}
                      onPause={() => setIsPlayingDemo(false)}
                    />
                  ) : (
                    <img
                      src="/sample-properties/1_exterior_facade.jpg"
                      alt="Greenview Residency Luxury Facade"
                      className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-700"
                    />
                  )}

                  {/* Gradient Overlay for Text Readability */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent pointer-events-none" />

                  {/* Sample Property Title & Price Overlays */}
                  <div className="absolute bottom-3 left-3 right-3 text-white pointer-events-none">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <div className="text-sm font-bold font-outfit drop-shadow">
                          Greenview Residency
                        </div>
                        <div className="text-[11px] text-slate-300 drop-shadow flex items-center gap-1">
                          Sector 82, Mohali, Punjab
                        </div>
                      </div>
                      <div className="px-2.5 py-1 rounded bg-[#344E8B]/90 backdrop-blur-sm text-white font-extrabold text-xs shadow">
                        ₹85 Lakh
                      </div>
                    </div>
                  </div>

                  {/* Functional Play Control Overlay */}
                  <button
                    type="button"
                    onClick={handleTogglePlay}
                    className="absolute inset-0 m-auto w-14 h-14 rounded-full bg-white/90 hover:bg-white text-[#344E8B] flex items-center justify-center shadow-xl transition-transform hover:scale-110 cursor-pointer z-10"
                    aria-label={isPlayingDemo ? 'Pause preview' : 'Play preview'}
                  >
                    {isPlayingDemo ? (
                      <Pause className="w-6 h-6 fill-current text-[#A93478]" />
                    ) : (
                      <Play className="w-6 h-6 fill-current text-[#344E8B] ml-1" />
                    )}
                  </button>
                </div>

                {/* Floating UI Element 1: AI Script Generation */}
                <div className="mt-3.5 p-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] flex items-start gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-[#344E8B] to-[#A93478] text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-[#292943]">AI Script Engine</span>
                      <span className="text-[10px] text-[#21865B] font-semibold flex items-center gap-0.5">
                        <Check className="w-3 h-3 stroke-[3]" /> Factual
                      </span>
                    </div>
                    <p className="text-[11px] text-[#686A7D] italic mt-0.5 line-clamp-1">
                      "Welcome to Greenview Residency, where contemporary elegance meets tranquil park views..."
                    </p>
                  </div>
                </div>

                {/* Floating UI Element 2: Storyboard Scene Sequencing */}
                <div className="mt-2.5 p-2.5 rounded-xl bg-white border border-[#E5E5EF]">
                  <div className="text-[10px] uppercase font-bold text-[#686A7D] mb-1.5 flex items-center justify-between">
                    <span>Scene Sequencing (Ken Burns)</span>
                    <span className="text-[#344E8B] font-semibold">30s Total</span>
                  </div>
                  <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-0.5">
                    <div className="px-2 py-1 rounded bg-[#344E8B]/10 text-[#344E8B] text-[10px] font-semibold flex-shrink-0 border border-[#344E8B]/20">
                      1. Facade (5s)
                    </div>
                    <div className="px-2 py-1 rounded bg-[#67417F]/10 text-[#67417F] text-[10px] font-semibold flex-shrink-0 border border-[#67417F]/20">
                      2. Living (5s)
                    </div>
                    <div className="px-2 py-1 rounded bg-[#A93478]/10 text-[#A93478] text-[10px] font-semibold flex-shrink-0 border border-[#A93478]/20">
                      3. Kitchen (5s)
                    </div>
                    <div className="px-2 py-1 rounded bg-[#344E8B]/10 text-[#344E8B] text-[10px] font-semibold flex-shrink-0 border border-[#344E8B]/20">
                      +3 more
                    </div>
                  </div>
                </div>

                {/* Floating UI Element 3: MP4 Export Specification */}
                <div className="mt-2.5 flex items-center justify-between px-3 py-2 rounded-xl bg-gradient-to-r from-[#344E8B]/5 to-[#A93478]/5 border border-[#E5E5EF] text-[11px]">
                  <div className="flex items-center gap-1.5 text-[#292943] font-semibold">
                    <Film className="w-3.5 h-3.5 text-[#344E8B]" />
                    <span>1080p Full HD • H.264 / AAC</span>
                  </div>
                  <span className="text-[10px] font-bold text-[#21865B] bg-[#21865B]/10 px-2 py-0.5 rounded">
                    Ready to Share
                  </span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 1: HOW IT WORKS                                       */}
      {/* ------------------------------------------------------------- */}
      <section id="how-it-works" className="py-16 sm:py-20 bg-white border-b border-[#E5E5EF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="text-xs font-bold uppercase tracking-wider text-[#344E8B] bg-[#344E8B]/10 px-3 py-1 rounded-full">
              Streamlined 3-Step Process
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold font-outfit text-[#292943] mt-3 mb-4">
              How RA Property Studio AI Works
            </h2>
            <p className="text-base text-[#686A7D]">
              Generate a high-converting promotional real estate video in under three minutes without any video editing experience.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {howItWorksSteps.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.step}
                  className="brand-card brand-card-hover p-6 sm:p-8 flex flex-col justify-between relative bg-white"
                >
                  {/* Top Step Number Badge */}
                  <div className="flex items-center justify-between mb-5">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-[#344E8B] via-[#67417F] to-[#A93478] text-white flex items-center justify-center font-outfit font-extrabold text-lg shadow-md">
                      0{item.step}
                    </div>
                    <span className="text-xs font-bold text-[#344E8B] bg-[#344E8B]/10 px-2.5 py-1 rounded-md">
                      {item.badge}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-xl font-bold font-outfit text-[#292943] mb-3">
                      {item.title}
                    </h3>
                    <p className="text-sm text-[#686A7D] leading-relaxed mb-6">
                      {item.desc}
                    </p>

                    <div className="space-y-2 pt-4 border-t border-[#E5E5EF]">
                      {item.features.map((feat, fIdx) => (
                        <div key={fIdx} className="flex items-center gap-2 text-xs text-[#292943]">
                          <CheckCircle2 className="w-3.5 h-3.5 text-[#21865B] flex-shrink-0" />
                          <span>{feat}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Centered Step Call-to-action */}
          <div className="text-center mt-12">
            <button
              onClick={onStart}
              className="brand-gradient-btn px-7 py-3.5 rounded-xl text-white font-bold text-sm inline-flex items-center gap-2 shadow-md cursor-pointer"
            >
              <span>Get Started Now</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 2: CORE FEATURES                                      */}
      {/* ------------------------------------------------------------- */}
      <section className="py-16 sm:py-20 bg-[#F7F7FC] border-b border-[#E5E5EF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="text-xs font-bold uppercase tracking-wider text-[#A93478] bg-[#A93478]/10 px-3 py-1 rounded-full">
              Enterprise Features
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold font-outfit text-[#292943] mt-3 mb-4">
              Engineered Specifically for Modern Real Estate
            </h2>
            <p className="text-base text-[#686A7D]">
              Everything you need to turn static property photographs into captivating video assets across social media and digital channels.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {featuresList.map((feat, idx) => {
              const Icon = feat.icon;
              return (
                <div
                  key={idx}
                  className="brand-card brand-card-hover p-6 bg-white flex flex-col justify-between"
                >
                  <div>
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-[#344E8B]/10 to-[#A93478]/10 text-[#344E8B] flex items-center justify-center mb-4 border border-[#E5E5EF]">
                      <Icon className="w-6 h-6 text-[#344E8B]" />
                    </div>
                    <h3 className="text-lg font-bold font-outfit text-[#292943] mb-2">
                      {feat.title}
                    </h3>
                    <p className="text-sm text-[#686A7D] leading-relaxed">
                      {feat.desc}
                    </p>
                  </div>
                  <div className="mt-4 pt-3 border-t border-[#E5E5EF] flex items-center gap-1.5 text-xs text-[#344E8B] font-semibold">
                    <span>Verified Production Pipeline</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 3: SAMPLE OUTPUT SHOWCASE (DEMO LABELED)              */}
      {/* ------------------------------------------------------------- */}
      <section className="py-16 sm:py-20 bg-white border-b border-[#E5E5EF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <span className="text-xs font-bold uppercase tracking-wider text-[#67417F] bg-[#67417F]/10 px-3 py-1 rounded-full">
              Demo Showcase
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold font-outfit text-[#292943] mt-3 mb-4">
              Explore Sample Output
            </h2>
            <p className="text-base text-[#686A7D]">
              Examine the sample property used to test and verify the studio pipeline. Click "Load Sample Listing" to immediately populate the creator with this listing.
            </p>
          </div>

          <div className="brand-card p-6 sm:p-8 bg-[#F7F7FC] border border-[#E5E5EF] max-w-5xl mx-auto">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5E5EF]">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 rounded bg-[#A93478]/15 text-[#A93478] font-bold text-xs uppercase tracking-wider">
                    Demo Property
                  </span>
                  <span className="text-xs text-[#686A7D]">• 6 Verified Images</span>
                </div>
                <h3 className="text-2xl font-bold font-outfit text-[#292943]">
                  Greenview Residency
                </h3>
                <p className="text-sm text-[#686A7D]">
                  Sector 82, Mohali, Punjab • ₹85 Lakh (2 BHK Luxury Apartment)
                </p>
              </div>

              <button
                type="button"
                onClick={onLoadSample}
                disabled={isLoadingSample}
                className="brand-gradient-btn px-6 py-3 rounded-xl text-white font-bold text-sm flex items-center justify-center gap-2 shadow-sm cursor-pointer disabled:opacity-50"
              >
                {isLoadingSample ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Loading...</span>
                  </>
                ) : (
                  <>
                    <Home className="w-4 h-4" />
                    <span>Load This Demo in Studio</span>
                  </>
                )}
              </button>
            </div>

            {/* Image Grid of Sample Photos */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-6">
              {sampleThumbnails.map((thumb, idx) => (
                <div key={idx} className="group relative rounded-xl overflow-hidden bg-slate-200 aspect-square border border-[#E5E5EF]">
                  <img
                    src={`/sample-properties/${thumb.name}`}
                    alt={thumb.label}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent flex items-end p-2">
                    <span className="text-[10px] font-semibold text-white leading-tight">
                      {thumb.label}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Specs bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-[#E5E5EF] text-center text-xs">
              <div className="p-3 rounded-lg bg-white border border-[#E5E5EF]">
                <span className="text-[#686A7D] block text-[10px] uppercase font-bold">Duration</span>
                <span className="font-extrabold text-[#292943] text-sm">30 Seconds</span>
              </div>
              <div className="p-3 rounded-lg bg-white border border-[#E5E5EF]">
                <span className="text-[#686A7D] block text-[10px] uppercase font-bold">Resolution</span>
                <span className="font-extrabold text-[#292943] text-sm">1920 × 1080 Full HD</span>
              </div>
              <div className="p-3 rounded-lg bg-white border border-[#E5E5EF]">
                <span className="text-[#686A7D] block text-[10px] uppercase font-bold">Voiceover</span>
                <span className="font-extrabold text-[#21865B] text-sm">Synchronized TTS</span>
              </div>
              <div className="p-3 rounded-lg bg-white border border-[#E5E5EF]">
                <span className="text-[#686A7D] block text-[10px] uppercase font-bold">Theme</span>
                <span className="font-extrabold text-[#344E8B] text-sm">Luxury Theme</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 4: FINAL CALL TO ACTION                               */}
      {/* ------------------------------------------------------------- */}
      <section className="py-16 sm:py-24 bg-gradient-to-r from-[#344E8B] via-[#67417F] to-[#A93478] text-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/15 backdrop-blur-md text-white text-xs font-semibold">
            <Film className="w-4 h-4 text-white" />
            <span>Every Property. A Story Worth Sharing.</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-extrabold font-outfit text-white tracking-tight leading-tight">
            Ready to Transform Your Listings Into High-Converting Videos?
          </h2>

          <p className="text-base sm:text-lg text-white/85 max-w-2xl mx-auto leading-relaxed">
            Generate promotional videos with broadcast-quality transitions, natural narration, and factual lower thirds in minutes.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <button
              onClick={onStart}
              className="bg-white text-[#344E8B] hover:bg-slate-100 font-extrabold px-8 py-4 rounded-xl text-base flex items-center justify-center gap-3 shadow-xl transition-all cursor-pointer w-full sm:w-auto"
            >
              <Video className="w-5 h-5 text-[#344E8B]" />
              <span>Create Property Video</span>
              <ArrowRight className="w-5 h-5 text-[#344E8B]" />
            </button>

            <button
              onClick={onLoadSample}
              disabled={isLoadingSample}
              className="bg-white/15 hover:bg-white/25 border border-white/30 text-white font-semibold px-7 py-4 rounded-xl text-base flex items-center justify-center gap-2 transition-all cursor-pointer w-full sm:w-auto"
            >
              <Home className="w-5 h-5 text-white" />
              <span>Explore Demo Listing</span>
            </button>
          </div>

          <div className="text-xs text-white/70 pt-6">
            RA Property Studio AI • by Realty Assistant | Part of Viraj Ventures
          </div>
        </div>
      </section>
    </div>
  );
}
