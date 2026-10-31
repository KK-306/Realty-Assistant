import React, { useState, useEffect } from 'react';
import {
  X,
  Film,
  Download,
  Play,
  Trash2,
  Calendar,
  Clock,
  Maximize2,
  CheckCircle2,
  ArrowRight,
  RefreshCw,
  Sparkles
} from 'lucide-react';

export default function MyVideosModal({ isOpen, onClose, onCreateNew, onLoadSample }) {
  const [activeVideo, setActiveVideo] = useState(null);
  const [videos, setVideos] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load and merge videos whenever the modal opens
  useEffect(() => {
    if (!isOpen) {
      setActiveVideo(null);
      return;
    }

    const loadVideos = async () => {
      setIsLoading(true);

      // 1. Get from localStorage
      let localList = [];
      try {
        const stored = localStorage.getItem('ra_property_studio_videos');
        if (stored) {
          localList = JSON.parse(stored);
        }
      } catch {
        localList = [];
      }

      // 2. Fetch from backend server API
      let serverList = [];
      try {
        const res = await fetch('/api/videos');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data.videos)) {
            serverList = data.videos;
          }
        }
      } catch {
        // server request failed, proceed with local
      }

      // 3. Merge unique by video_id
      const map = new Map();
      // First add local (which has custom user property names)
      for (const v of localList) {
        if (v && v.video_id) {
          map.set(v.video_id, v);
        }
      }
      // Then add any server-rendered videos not yet in local
      for (const s of serverList) {
        if (s && s.video_id && !map.has(s.video_id)) {
          map.set(s.video_id, s);
        }
      }

      const combined = Array.from(map.values());
      setVideos(combined);
      setIsLoading(false);
    };

    loadVideos();
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleDelete = (videoId, e) => {
    e.stopPropagation();
    const updated = videos.filter((v) => v.video_id !== videoId);
    setVideos(updated);
    try {
      localStorage.setItem('ra_property_studio_videos', JSON.stringify(updated));
    } catch {
      // ignore
    }
    if (activeVideo?.video_id === videoId) {
      setActiveVideo(null);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Recent';
    try {
      const d = new Date(dateString);
      return isNaN(d.getTime()) ? 'Recent' : d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return 'Recent';
    }
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-white rounded-2xl w-full max-w-3xl shadow-2xl border border-[#E5E5EF] overflow-hidden flex flex-col max-h-[85vh] animate-scale-in"
      >
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-[#344E8B] via-[#67417F] to-[#A93478] text-white flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center">
              <Film className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 id="modal-title" className="text-lg font-bold font-outfit text-white">
                My Generated Videos
              </h2>
              <p className="text-xs text-white/80">
                Browse, preview, and download your promotional property videos
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors cursor-pointer"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto flex-1">
          {/* Active Inline Video Player */}
          {activeVideo && (
            <div className="mb-6 p-4 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#21865B] animate-pulse" />
                  <span className="text-xs font-bold text-[#292943] uppercase tracking-wider line-clamp-1">
                    Playing: {activeVideo.property_name || 'Property Showcase'}
                  </span>
                </div>
                <button
                  onClick={() => setActiveVideo(null)}
                  className="text-xs font-semibold text-[#A93478] hover:underline cursor-pointer"
                >
                  Close Player
                </button>
              </div>
              <div className="aspect-video bg-black rounded-lg overflow-hidden shadow-inner border border-slate-300">
                <video
                  src={`/api/videos/${encodeURIComponent(activeVideo.video_id)}/stream`}
                  controls
                  autoPlay
                  className="w-full h-full object-contain"
                >
                  Your browser does not support HTML5 video.
                </video>
              </div>
            </div>
          )}

          {isLoading ? (
            <div className="py-16 text-center text-[#686A7D]">
              <div className="w-8 h-8 border-3 border-[#344E8B] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-xs font-semibold">Loading your video library...</p>
            </div>
          ) : videos.length === 0 ? (
            /* Empty State */
            <div className="text-center py-12 px-4">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-tr from-[#344E8B]/10 to-[#A93478]/10 border border-[#E5E5EF] flex items-center justify-center text-[#344E8B]">
                <Film className="w-8 h-8 stroke-[1.5]" />
              </div>
              <h3 className="text-xl font-bold font-outfit text-[#292943] mb-2">
                No videos generated yet
              </h3>
              <p className="text-sm text-[#686A7D] max-w-md mx-auto mb-6">
                Transform property images and facts into cinematic marketing videos in seconds.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                <button
                  onClick={() => {
                    onClose();
                    onCreateNew();
                  }}
                  className="brand-gradient-btn px-5 py-2.5 rounded-xl text-sm flex items-center gap-2 cursor-pointer shadow-sm"
                >
                  <Film className="w-4 h-4" />
                  <span>Create Property Video</span>
                </button>
                <button
                  onClick={() => {
                    onClose();
                    onLoadSample();
                  }}
                  className="brand-outline-btn px-5 py-2.5 rounded-xl text-sm flex items-center gap-2 cursor-pointer"
                >
                  <span>Explore Demo Listing</span>
                </button>
              </div>
            </div>
          ) : (
            /* Video List */
            <div className="space-y-3">
              {videos.map((vid) => (
                <div
                  key={vid.video_id}
                  onClick={() => setActiveVideo(vid)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                    activeVideo?.video_id === vid.video_id
                      ? 'border-[#344E8B] bg-[#344E8B]/5 shadow-sm'
                      : 'border-[#E5E5EF] hover:border-[#344E8B]/40 hover:bg-[#F7F7FC]'
                  }`}
                >
                  <div className="flex items-center gap-3.5">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-tr from-[#344E8B] to-[#A93478] text-white flex items-center justify-center flex-shrink-0 shadow-sm">
                      <Play className="w-5 h-5 fill-current ml-0.5" />
                    </div>
                    <div>
                      <h4 className="font-bold text-[#292943] text-sm sm:text-base font-outfit line-clamp-1">
                        {vid.property_name || 'Promotional Property Video'}
                      </h4>
                      <p className="text-xs text-[#686A7D] line-clamp-1 mt-0.5">
                        {vid.location || 'Featured Real Estate Listing'}
                      </p>
                      <div className="flex items-center gap-2 mt-1.5 text-[11px] text-[#686A7D]">
                        <span className="inline-flex items-center gap-1 font-semibold text-[#344E8B]">
                          <Clock className="w-3 h-3" />
                          {vid.duration ? `${vid.duration}s` : '30s'}
                        </span>
                        <span>•</span>
                        <span className="inline-flex items-center gap-1 font-semibold text-[#67417F]">
                          <Maximize2 className="w-3 h-3" />
                          {vid.aspect_ratio || '16:9'}
                        </span>
                        <span>•</span>
                        <span className="inline-flex items-center gap-1 text-[#686A7D]">
                          <Calendar className="w-3 h-3 text-[#A93478]" />
                          {formatDate(vid.date || vid.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveVideo(vid);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-[#344E8B]/10 hover:bg-[#344E8B]/20 text-[#344E8B] text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>Preview</span>
                    </button>

                    <a
                      href={vid.download_url || `/api/videos/${vid.video_id}/download`}
                      download
                      onClick={(e) => e.stopPropagation()}
                      className="px-3 py-1.5 rounded-lg brand-gradient-btn text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                      title="Download MP4"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download</span>
                    </a>

                    <button
                      type="button"
                      onClick={(e) => handleDelete(vid.video_id, e)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-[#C53C53] hover:bg-red-50 transition-colors cursor-pointer"
                      title="Remove from list"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-[#F7F7FC] border-t border-[#E5E5EF] flex items-center justify-between text-xs text-[#686A7D]">
          <span className="font-medium">
            {videos.length} {videos.length === 1 ? 'Video' : 'Videos'} Available
          </span>
          <button
            onClick={() => {
              onClose();
              onCreateNew();
            }}
            className="brand-gradient-btn px-3.5 py-1.5 rounded-lg text-xs flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <Film className="w-3.5 h-3.5" />
            <span>Create New Video</span>
          </button>
        </div>
      </div>
    </div>
  );
}
