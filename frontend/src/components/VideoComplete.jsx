import React, { useState } from 'react';
import {
  Download,
  RefreshCw,
  Plus,
  Film,
  Check,
  FileVideo,
  Share2,
  Clock,
  Maximize2,
  HardDrive,
  CheckCircle2,
  Sparkles
} from 'lucide-react';

export default function VideoComplete({
  videoJob,
  formData,
  onReset,
  onRegenerate,
}) {
  const [copied, setCopied] = useState(false);

  const videoId = videoJob?.video_id || videoJob?.job_id;
  const streamUrl = videoJob?.video_url || `/api/videos/${videoId}/stream`;
  const downloadUrl = videoJob?.download_url || `/api/videos/${videoId}/download`;
  const metadata = videoJob?.metadata;

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    const mb = bytes / (1024 * 1024);
    if (mb < 1) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${mb.toFixed(2)} MB`;
  };

  const handleShare = async () => {
    const fullDownloadUrl = `${window.location.origin}${downloadUrl}`;
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(fullDownloadUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }
  };

  const isVertical = metadata?.aspect_ratio === '9:16' || formData?.aspect_ratio === '9:16';

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8 animate-fade-in">
      {/* Success Celebration Banner */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#21865B]/15 border border-[#21865B]/30 text-[#21865B] mb-4">
          <Check className="w-8 h-8 stroke-[3]" />
        </div>

        <div className="flex items-center justify-center gap-2 mb-2">
          <Film className="w-4 h-4 text-[#344E8B]" />
          <span className="text-xs font-bold uppercase tracking-wider text-[#344E8B]">
            Rendering Complete
          </span>
          <Film className="w-4 h-4 text-[#A93478]" />
        </div>

        <h1 className="text-3xl sm:text-4xl font-extrabold font-outfit text-[#292943] mb-2">
          Your Promotional Video is Ready!
        </h1>
        <p className="text-sm sm:text-base text-[#686A7D] max-w-lg mx-auto">
          Broadcast-grade property video with motion effects, branding overlays, and audio track.
        </p>
      </div>

      {/* Main Video Card & Player */}
      <div className="brand-card rounded-3xl p-6 sm:p-8 mb-8 bg-white border border-[#E5E5EF] shadow-2xl relative overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Video Player Column */}
          <div className={`lg:col-span-7 flex flex-col items-center justify-center ${isVertical ? 'max-w-sm mx-auto' : 'w-full'}`}>
            <div className={`w-full rounded-2xl overflow-hidden bg-black border border-slate-300 shadow-2xl relative ${
              isVertical ? 'aspect-[9/16]' : 'aspect-video'
            }`}>
              <video
                src={streamUrl}
                controls
                autoPlay
                playsInline
                className="w-full h-full object-contain bg-black"
                poster="/api/samples/images/2_living_room.jpg"
              >
                Your browser does not support HTML5 video playback.
              </video>
            </div>
            <div className="text-center mt-3 text-xs text-[#686A7D]">
              HTML5 High-Definition MP4 Player
            </div>
          </div>

          {/* Details & Actions Column */}
          <div className="lg:col-span-5 flex flex-col justify-between space-y-6">
            {/* Property Summary Pill */}
            <div className="p-4 rounded-2xl bg-[#F7F7FC] border border-[#E5E5EF]">
              <span className="text-[10px] uppercase tracking-wider font-bold text-[#344E8B] block mb-1">
                Property Showcase
              </span>
              <h3 className="text-xl font-bold font-outfit text-[#292943]">
                {formData?.property_name || 'Featured Property'}
              </h3>
              <p className="text-xs text-[#686A7D] mt-0.5">
                {formData?.location || 'Prime Location'}
              </p>

              {(formData?.price_display || formData?.price) && (
                <div className="mt-3 inline-block px-3 py-1 rounded-lg bg-[#344E8B]/10 border border-[#344E8B]/25 text-[#344E8B] font-extrabold text-sm">
                  {formData?.price_display || `${formData?.currency || '₹'} ${Number(formData?.price).toLocaleString()}`}
                </div>
              )}
            </div>

            {/* Video Specs Metadata Grid */}
            <div>
              <h4 className="text-xs uppercase font-bold tracking-wider text-[#686A7D] mb-3 flex items-center gap-1.5">
                <FileVideo className="w-4 h-4 text-[#344E8B]" />
                <span>Video Specifications</span>
              </h4>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF]">
                  <div className="text-[#686A7D] text-[10px] uppercase font-bold flex items-center gap-1">
                    <Clock className="w-3 h-3 text-[#344E8B]" />
                    <span>Duration</span>
                  </div>
                  <div className="font-bold text-[#292943] mt-1 text-sm">
                    {metadata?.duration_seconds ? `${metadata.duration_seconds}s` : `${formData?.duration || 30}s`}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF]">
                  <div className="text-[#686A7D] text-[10px] uppercase font-bold flex items-center gap-1">
                    <Maximize2 className="w-3 h-3 text-[#67417F]" />
                    <span>Resolution</span>
                  </div>
                  <div className="font-bold text-[#292943] mt-1 text-sm">
                    {metadata?.width && metadata?.height ? `${metadata.width} × ${metadata.height}` : isVertical ? '1080 × 1920' : '1920 × 1080'}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF]">
                  <div className="text-[#686A7D] text-[10px] uppercase font-bold flex items-center gap-1">
                    <HardDrive className="w-3 h-3 text-[#A93478]" />
                    <span>File Size</span>
                  </div>
                  <div className="font-bold text-[#292943] mt-1 text-sm">
                    {formatFileSize(metadata?.file_size_bytes)}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF]">
                  <div className="text-[#686A7D] text-[10px] uppercase font-bold flex items-center gap-1">
                    <FileVideo className="w-3 h-3 text-[#21865B]" />
                    <span>Format & FPS</span>
                  </div>
                  <div className="font-bold text-[#292943] mt-1 text-sm">
                    {(metadata?.format || 'mp4').toUpperCase()} • {metadata?.fps || 30} FPS
                  </div>
                </div>
              </div>
            </div>

            {/* Primary Action: Download Button */}
            <div className="space-y-3 pt-2">
              <a
                href={downloadUrl}
                download
                className="brand-gradient-btn w-full py-4 px-6 rounded-xl text-white font-bold text-base flex items-center justify-center gap-3 shadow-lg cursor-pointer no-underline text-center"
              >
                <Download className="w-5 h-5 text-white" />
                <span>Download MP4 Video</span>
              </a>

              <button
                type="button"
                onClick={handleShare}
                className="w-full py-3 px-4 rounded-xl border border-[#E5E5EF] bg-white hover:border-[#344E8B] text-[#292943] font-semibold text-xs flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                {copied ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-[#21865B]" />
                    <span className="text-[#21865B] font-bold">Link Copied to Clipboard!</span>
                  </>
                ) : (
                  <>
                    <Share2 className="w-4 h-4 text-[#686A7D]" />
                    <span>Copy Download Link</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Navigation Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-4 border-t border-[#E5E5EF]">
        <button
          type="button"
          onClick={onRegenerate}
          className="w-full sm:w-auto px-6 py-3.5 rounded-xl border border-[#E5E5EF] bg-white text-[#686A7D] hover:text-[#292943] hover:border-[#344E8B] font-semibold text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Adjust & Regenerate</span>
        </button>

        <button
          type="button"
          onClick={onReset}
          className="w-full sm:w-auto px-8 py-3.5 rounded-xl brand-gradient-btn text-white font-bold text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-md"
        >
          <Plus className="w-4 h-4 text-white" />
          <span>Create Another Video</span>
        </button>
      </div>
    </div>
  );
}
