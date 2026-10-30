import React, { useState, useEffect, useRef } from 'react';
import {
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Film,
  RefreshCw,
  Sparkles
} from 'lucide-react';

export default function VideoGenerating({
  jobId,
  onVideoReady,
  onRetry,
  onBackToEdit,
}) {
  const [job, setJob] = useState({
    job_id: jobId,
    status: 'queued',
    progress_percent: 5,
    stage_message: 'Initializing video generation pipeline...',
  });
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [pollError, setPollError] = useState(null);

  // Timer ref
  const timerRef = useRef(null);
  const pollRef = useRef(null);

  // Start elapsed timer
  useEffect(() => {
    timerRef.current = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Poll Job Status every 2 seconds
  useEffect(() => {
    let isCancelled = false;

    const pollJob = async () => {
      if (!jobId) return;

      try {
        const res = await fetch(`/api/videos/jobs/${jobId}`);
        if (!res.ok) {
          throw new Error(`Failed to fetch job status (${res.status})`);
        }

        const data = await res.json();
        if (isCancelled) return;

        setJob(data);
        setPollError(null);

        if (data.status === 'completed') {
          if (timerRef.current) clearInterval(timerRef.current);
          if (pollRef.current) clearInterval(pollRef.current);
          // Allow user to see 100% completion briefly before advancing
          setTimeout(() => {
            onVideoReady(data);
          }, 600);
        } else if (data.status === 'failed') {
          if (timerRef.current) clearInterval(timerRef.current);
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch (err) {
        if (!isCancelled) {
          setPollError(err.message || 'Network error while checking status');
        }
      }
    };

    // Run first check immediately
    pollJob();

    // Then interval every 2000ms
    pollRef.current = setInterval(pollJob, 2000);

    return () => {
      isCancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [jobId, onVideoReady]);

  // Format MM:SS
  const formatTime = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const stages = [
    { key: 'queued', label: 'Queued', step: 1 },
    { key: 'validating', label: 'Validating Assets', step: 2 },
    { key: 'scripting', label: 'Audio & Narration', step: 3 },
    { key: 'preparing', label: 'Motion & Ken Burns', step: 4 },
    { key: 'rendering', label: 'Video Rendering', step: 5 },
    { key: 'finalizing', label: 'MP4 Encoding', step: 6 },
  ];

  const getStageIndex = (currentStatus) => {
    const idx = stages.findIndex((s) => s.key === currentStatus);
    if (idx !== -1) return idx;
    if (currentStatus === 'completed') return stages.length;
    return 0;
  };

  const currentStageIndex = getStageIndex(job.status);
  const isFailed = job.status === 'failed';

  return (
    <div className="max-w-3xl mx-auto py-12 px-4 sm:px-6 lg:px-8 animate-fade-in">
      <div className="brand-card p-8 sm:p-12 text-center relative overflow-hidden bg-white border border-[#E5E5EF] shadow-2xl rounded-3xl">
        {/* Subtle Brand Background Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-gradient-to-tr from-[#344E8B]/10 to-[#A93478]/10 blur-[90px] rounded-full pointer-events-none -z-10" />

        {/* Failed State */}
        {isFailed ? (
          <div className="space-y-6">
            <div className="w-20 h-20 mx-auto rounded-3xl bg-red-50 border border-[#C53C53]/40 flex items-center justify-center text-[#C53C53]">
              <XCircle className="w-10 h-10" />
            </div>

            <div>
              <h2 className="text-2xl font-bold font-outfit text-[#292943] mb-2">
                Video Generation Encountered an Issue
              </h2>
              <p className="text-sm text-[#C53C53] max-w-lg mx-auto">
                {job.error_message || 'The render engine encountered an unexpected issue while synthesizing your video.'}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <button
                type="button"
                onClick={onRetry}
                className="brand-gradient-btn px-6 py-3.5 rounded-xl text-white font-bold text-sm flex items-center gap-2 cursor-pointer shadow-lg"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Retry Generation</span>
              </button>

              <button
                type="button"
                onClick={onBackToEdit}
                className="px-6 py-3.5 rounded-xl border border-[#E5E5EF] bg-white text-[#686A7D] hover:text-[#292943] hover:border-[#344E8B] font-semibold text-sm transition-colors cursor-pointer"
              >
                Back to Edit Form
              </button>
            </div>
          </div>
        ) : (
          /* Active Generation State */
          <div className="space-y-8">
            {/* Spinning Indicator */}
            <div className="relative w-32 h-32 mx-auto flex items-center justify-center">
              {/* Outer decorative ring */}
              <div className="absolute inset-0 rounded-full border-4 border-[#E5E5EF]" />
              {/* Spinning progress border */}
              <div
                className="absolute inset-0 rounded-full border-4 border-[#344E8B] border-t-transparent animate-spin"
                style={{ animationDuration: '1.8s' }}
              />
              {/* Center icon / percent */}
              <div className="flex flex-col items-center justify-center">
                <span className="text-2xl font-black font-outfit text-[#292943]">
                  {job.progress_percent}%
                </span>
                <span className="text-[10px] uppercase tracking-wider text-[#A93478] font-bold">
                  Progress
                </span>
              </div>
            </div>

            {/* Title & Stage Message */}
            <div>
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#344E8B]/10 border border-[#344E8B]/20 text-[#344E8B] text-xs font-bold mb-3">
                <Film className="w-3.5 h-3.5 text-[#344E8B]" />
                <span>Rendering High-Definition Video</span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-extrabold font-outfit text-[#292943] mb-2">
                Creating Your Property Showcase
              </h2>

              <p className="text-sm text-[#686A7D] max-w-md mx-auto min-h-[2.5rem] flex items-center justify-center font-medium">
                {job.stage_message || 'Processing frames, Ken Burns zoom motion, and audio tracks...'}
              </p>
            </div>

            {/* Horizontal Progress Bar */}
            <div className="max-w-md mx-auto space-y-2">
              <div className="w-full h-3 rounded-full bg-[#E5E5EF] overflow-hidden p-0.5">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#344E8B] via-[#67417F] to-[#A93478] transition-all duration-500 ease-out"
                  style={{ width: `${Math.min(100, Math.max(5, job.progress_percent))}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-xs text-[#686A7D] px-1">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-[#344E8B]" />
                  Elapsed: <strong className="text-[#292943]">{formatTime(elapsedSeconds)}</strong>
                </span>
                <span className="capitalize">
                  Status: <strong className="text-[#344E8B]">{job.status}</strong>
                </span>
              </div>
            </div>

            {/* Stage Timeline */}
            <div className="pt-6 border-t border-[#E5E5EF] max-w-lg mx-auto">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-left">
                {stages.map((stg, i) => {
                  const isDone = i < currentStageIndex || job.status === 'completed';
                  const isCurrent = i === currentStageIndex && job.status !== 'completed';

                  return (
                    <div
                      key={stg.key}
                      className={`p-2.5 rounded-xl border text-xs transition-all ${
                        isDone
                          ? 'bg-[#21865B]/10 border-[#21865B]/30 text-[#21865B]'
                          : isCurrent
                          ? 'bg-[#344E8B]/10 border-[#344E8B]/40 text-[#344E8B] ring-1 ring-[#344E8B]/20'
                          : 'bg-[#F7F7FC] border-[#E5E5EF] text-[#686A7D]'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-bold">0{stg.step}</span>
                        {isDone ? (
                          <CheckCircle className="w-3.5 h-3.5 text-[#21865B]" />
                        ) : isCurrent ? (
                          <Loader2 className="w-3.5 h-3.5 text-[#344E8B] animate-spin" />
                        ) : (
                          <div className="w-2 h-2 rounded-full bg-slate-300" />
                        )}
                      </div>
                      <div className="font-bold truncate">{stg.label}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Poll Warning Banner if any */}
            {pollError && (
              <p className="text-xs text-[#A93478] bg-rose-50 border border-rose-200 py-1.5 px-3 rounded-lg max-w-sm mx-auto">
                Reconnecting: {pollError}
              </p>
            )}

            {/* Informational tip */}
            <p className="text-xs text-[#686A7D] pt-2">
              Tip: Pipeline performs AI script refinement, image pan & zoom, voiceover synthesis, and FFmpeg video compositing. Please keep this tab open.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
