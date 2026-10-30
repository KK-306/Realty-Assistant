import React, { useState, useRef } from 'react';
import {
  Upload,
  X,
  GripVertical,
  Plus,
  Image as ImageIcon,
  MapPin,
  DollarSign,
  Home,
  Building,
  Palette,
  Clock,
  Smartphone,
  Monitor,
  Volume2,
  Mic,
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
  Sparkles,
  Phone,
  User,
  FileText
} from 'lucide-react';

export default function PropertyForm({
  initialData,
  uploadedImages: propImages,
  onStoryboardReady,
  onBack,
}) {
  // Form State
  const [formData, setFormData] = useState({
    property_name: initialData?.property_name || '',
    location: initialData?.location || '',
    price: initialData?.price ? String(initialData.price) : '',
    currency: initialData?.currency || '₹',
    price_display: initialData?.price_display || '',
    property_type: initialData?.property_type || 'apartment',
    key_features: initialData?.key_features?.length ? [...initialData.key_features] : [],
    bedrooms: initialData?.bedrooms !== undefined && initialData?.bedrooms !== null ? String(initialData.bedrooms) : '2',
    bathrooms: initialData?.bathrooms !== undefined && initialData?.bathrooms !== null ? String(initialData.bathrooms) : '2',
    description: initialData?.description || '',
    contact_name: initialData?.contact_name || 'Sales Team',
    contact_details: initialData?.contact_details || '',
    cta_text: initialData?.cta_text || 'Schedule a Visit',
    duration: initialData?.duration || 30,
    aspect_ratio: initialData?.aspect_ratio || '16:9',
    theme: initialData?.theme || 'luxury',
    voice_accent: initialData?.voice_accent || 'en-US-BrianNeural',
    narration_enabled: initialData?.narration_enabled !== undefined ? initialData.narration_enabled : true,
    music_enabled: initialData?.music_enabled !== undefined ? initialData.music_enabled : true,
  });

  // Images state
  const [images, setImages] = useState(
    propImages?.length
      ? propImages.map((img) => ({
          ...img,
          status: img.status || 'success',
        }))
      : []
  );

  // New feature input state
  const [newFeature, setNewFeature] = useState('');

  // UI / Validation state
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');
  const [isDraggingOver, setIsDraggingOver] = useState(false);

  // Drag-and-drop reordering state
  const dragItem = useRef(null);
  const dragOverItem = useRef(null);

  // File input ref
  const fileInputRef = useRef(null);

  // Helpers
  const formatBytes = (bytes, decimals = 1) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    if (errors[name]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  // Add Feature Chip
  const handleAddFeature = (e) => {
    if (e) e.preventDefault();
    const trimmed = newFeature.trim();
    if (!trimmed) return;
    if (formData.key_features.includes(trimmed)) {
      setNewFeature('');
      return;
    }
    if (formData.key_features.length >= 15) {
      setErrors((prev) => ({ ...prev, key_features: 'Maximum 15 features allowed.' }));
      return;
    }
    setFormData((prev) => ({
      ...prev,
      key_features: [...prev.key_features, trimmed],
    }));
    setNewFeature('');
    if (errors.key_features) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next.key_features;
        return next;
      });
    }
  };

  const handleRemoveFeature = (indexToRemove) => {
    setFormData((prev) => ({
      ...prev,
      key_features: prev.key_features.filter((_, idx) => idx !== indexToRemove),
    }));
  };

  // Image Upload Handling
  const handleFiles = async (fileList) => {
    setApiError('');
    const files = Array.from(fileList);
    const validFormats = ['image/jpeg', 'image/png', 'image/webp'];
    const maxSizeBytes = 15 * 1024 * 1024;

    const remainingSlots = 8 - images.length;
    if (remainingSlots <= 0) {
      setErrors((prev) => ({ ...prev, images: 'Maximum 8 images reached.' }));
      return;
    }

    const filesToUpload = files.slice(0, remainingSlots);

    for (const file of filesToUpload) {
      if (!validFormats.includes(file.type)) {
        setErrors((prev) => ({
          ...prev,
          images: `Invalid file format for "${file.name}". JPEG, PNG, and WebP only.`,
        }));
        continue;
      }

      if (file.size > maxSizeBytes) {
        setErrors((prev) => ({
          ...prev,
          images: `File "${file.name}" exceeds maximum allowed size of 15MB.`,
        }));
        continue;
      }

      const tempId = 'temp_' + Math.random().toString(36).substring(2, 9);
      const localPreviewUrl = URL.createObjectURL(file);

      const placeholderItem = {
        image_id: tempId,
        filename: file.name,
        original_filename: file.name,
        size_bytes: file.size,
        preview_url: localPreviewUrl,
        status: 'uploading',
        temp: true,
      };

      setImages((prev) => [...prev, placeholderItem]);

      // Upload in background
      const formDataUpload = new FormData();
      formDataUpload.append('file', file);

      try {
        const res = await fetch('/api/images/upload', {
          method: 'POST',
          body: formDataUpload,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Image upload failed');
        }

        const uploadedData = await res.json();

        setImages((prev) =>
          prev.map((img) =>
            img.image_id === tempId
              ? {
                  ...uploadedData,
                  status: 'success',
                  preview_url: uploadedData.preview_url || localPreviewUrl,
                }
              : img
          )
        );
      } catch (err) {
        setImages((prev) =>
          prev.map((img) =>
            img.image_id === tempId
              ? {
                  ...img,
                  status: 'error',
                  errorMessage: err.message || 'Failed to upload',
                }
              : img
          )
        );
      }
    }

    if (errors.images) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next.images;
        return next;
      });
    }
  };

  const handleRemoveImage = (imageId) => {
    setImages((prev) => prev.filter((img) => img.image_id !== imageId));
  };

  // Drag and drop reordering
  const handleDragStart = (e, index) => {
    dragItem.current = index;
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragEnter = (e, index) => {
    dragOverItem.current = index;
  };

  const handleDragEnd = () => {
    if (
      dragItem.current !== null &&
      dragOverItem.current !== null &&
      dragItem.current !== dragOverItem.current
    ) {
      const copy = [...images];
      const draggedItemContent = copy[dragItem.current];
      copy.splice(dragItem.current, 1);
      copy.splice(dragOverItem.current, 0, draggedItemContent);
      setImages(copy);
    }
    dragItem.current = null;
    dragOverItem.current = null;
  };

  // Drag and drop over zone
  const handleDropZoneOver = (e) => {
    e.preventDefault();
    setIsDraggingOver(true);
  };

  const handleDropZoneLeave = (e) => {
    e.preventDefault();
    setIsDraggingOver(false);
  };

  const handleDropZoneDrop = (e) => {
    e.preventDefault();
    setIsDraggingOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  // Validation
  const validateForm = () => {
    const newErrors = {};

    if (!formData.property_name.trim()) {
      newErrors.property_name = 'Property name is required (min 2 characters).';
    } else if (formData.property_name.trim().length < 2) {
      newErrors.property_name = 'Property name must be at least 2 characters.';
    }

    if (!formData.location.trim()) {
      newErrors.location = 'Location is required (city, locality).';
    } else if (formData.location.trim().length < 2) {
      newErrors.location = 'Location must be at least 2 characters.';
    }

    const priceNum = parseFloat(formData.price);
    if (!formData.price || isNaN(priceNum) || priceNum <= 0) {
      newErrors.price = 'Please enter a valid positive price amount.';
    }

    if (!formData.key_features || formData.key_features.length === 0) {
      newErrors.key_features = 'Add at least one key feature.';
    }

    if (!['plot', 'commercial'].includes(formData.property_type)) {
      if (formData.bedrooms !== '' && parseInt(formData.bedrooms, 10) < 0) {
        newErrors.bedrooms = 'Bedrooms cannot be negative.';
      }
      if (formData.bathrooms !== '' && parseInt(formData.bathrooms, 10) < 0) {
        newErrors.bathrooms = 'Bathrooms cannot be negative.';
      }
    }

    // Image validations
    const validImages = images.filter((img) => img.status === 'success' || !img.temp);
    if (validImages.length < 4) {
      newErrors.images = `At least 4 images are required (currently ${validImages.length}).`;
    } else if (validImages.length > 8) {
      newErrors.images = `A maximum of 8 images is allowed (currently ${validImages.length}).`;
    }

    const hasUploading = images.some((img) => img.status === 'uploading');
    if (hasUploading) {
      newErrors.images = 'Please wait for all images to finish uploading.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Submit Handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError('');

    if (!validateForm()) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    setIsSubmitting(true);

    try {
      const validImages = images.filter((img) => img.status === 'success' || !img.temp);
      const imageIds = validImages.map((img) => img.image_id);

      const priceNum = parseFloat(formData.price);
      const isResidential = !['plot', 'commercial'].includes(formData.property_type);

      const payload = {
        property_name: formData.property_name.trim(),
        location: formData.location.trim(),
        price: priceNum,
        currency: formData.currency.trim() || '₹',
        price_display: formData.price_display.trim() || undefined,
        property_type: formData.property_type,
        key_features: formData.key_features,
        bedrooms: isResidential && formData.bedrooms !== '' ? parseInt(formData.bedrooms, 10) : undefined,
        bathrooms: isResidential && formData.bathrooms !== '' ? parseInt(formData.bathrooms, 10) : undefined,
        description: formData.description.trim() || undefined,
        contact_name: formData.contact_name.trim() || 'Sales Team',
        contact_details: formData.contact_details.trim() || undefined,
        cta_text: formData.cta_text.trim() || 'Schedule a Visit',
        duration: parseInt(formData.duration, 10),
        aspect_ratio: formData.aspect_ratio,
        theme: formData.theme,
        voice_accent: formData.voice_accent,
        narration_enabled: Boolean(formData.narration_enabled),
        music_enabled: Boolean(formData.music_enabled),
        image_ids: imageIds,
      };

      // 1. Validate property with backend
      const valRes = await fetch('/api/properties/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!valRes.ok) {
        const errorData = await valRes.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Validation failed on server.');
      }

      const valData = await valRes.json();
      if (!valData.valid) {
        const msg = valData.errors?.join(', ') || valData.message || 'Validation failed.';
        throw new Error(msg);
      }

      // 2. Generate Storyboard
      const storyRes = await fetch('/api/storyboards/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!storyRes.ok) {
        const errorData = await storyRes.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to generate storyboard.');
      }

      const storyboard = await storyRes.json();

      // Pass ready data up
      onStoryboardReady(storyboard, payload, validImages);
    } catch (err) {
      setApiError(err.message || 'An error occurred during submission.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const themes = [
    {
      id: 'luxury',
      name: 'Luxury Prestige',
      desc: 'Gold & black palette, serif titles, regal pacing',
      badgeColor: 'border-amber-500/50 bg-amber-500/10 text-amber-300',
      preview: 'from-amber-600/30 to-amber-950/60',
    },
    {
      id: 'modern',
      name: 'Modern Neo',
      desc: 'Cyan & emerald tones, bold sans-serif, high energy',
      badgeColor: 'border-cyan-500/50 bg-cyan-500/10 text-cyan-300',
      preview: 'from-cyan-600/30 to-slate-900',
    },
    {
      id: 'minimal',
      name: 'Minimal Pure',
      desc: 'Monochrome slate, high contrast, clean architectural lines',
      badgeColor: 'border-slate-400/50 bg-slate-500/10 text-slate-300',
      preview: 'from-slate-600/30 to-slate-950',
    },
    {
      id: 'elegant',
      name: 'Elegant Warm',
      desc: 'Warm rose & ivory accents, smooth subtle transitions',
      badgeColor: 'border-rose-400/50 bg-rose-500/10 text-rose-300',
      preview: 'from-rose-600/30 to-amber-950/40',
    },
  ];

  const showBedBath = !['plot', 'commercial'].includes(formData.property_type);

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8 animate-fade-in">
      {/* Top Bar */}
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-[#E5E5EF]">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-2 text-sm text-[#686A7D] hover:text-[#292943] transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Home</span>
        </button>

        <div className="text-right">
          <span className="text-xs uppercase font-bold tracking-wider text-[#344E8B]">Step 1 of 3</span>
          <h2 className="text-lg font-bold font-outfit text-[#292943]">Property Details & Assets</h2>
        </div>
      </div>

      {/* Global API Error Alert */}
      {apiError && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-[#C53C53]/40 flex items-start gap-3 text-[#C53C53]">
          <AlertCircle className="w-5 h-5 text-[#C53C53] shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm">Submission Error</h4>
            <p className="text-xs text-[#C53C53]/90 mt-1">{apiError}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* SECTION 1: PROPERTY OVERVIEW */}
        <div className="brand-card p-6 sm:p-8 bg-white border border-[#E5E5EF] shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-lg bg-[#344E8B]/10 border border-[#344E8B]/20 flex items-center justify-center text-[#344E8B]">
              <Home className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold font-outfit text-[#292943]">Listing Essentials</h3>
              <p className="text-xs text-[#686A7D]">Key property identity and location specifications</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Property Name */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2">
                Property Name <span className="text-[#A93478]">*</span>
              </label>
              <input
                type="text"
                name="property_name"
                value={formData.property_name}
                onChange={handleInputChange}
                placeholder="e.g. Greenview Residency"
                className={`w-full px-4 py-3 rounded-xl bg-[#F7F7FC] border ${
                  errors.property_name ? 'border-[#C53C53] ring-1 ring-[#C53C53]' : 'border-[#E5E5EF] focus:border-[#344E8B]'
                } text-[#292943] placeholder-[#A3A7BE] text-sm focus:outline-none transition-colors`}
              />
              {errors.property_name && (
                <p className="text-xs text-[#C53C53] mt-1.5 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{errors.property_name}</span>
                </p>
              )}
            </div>

            {/* Location */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2">
                Location <span className="text-[#A93478]">*</span>
              </label>
              <div className="relative">
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  placeholder="e.g. Sector 82, Mohali, Punjab"
                  className={`w-full pl-10 pr-4 py-3 rounded-xl bg-[#F7F7FC] border ${
                    errors.location ? 'border-[#C53C53] ring-1 ring-[#C53C53]' : 'border-[#E5E5EF] focus:border-[#344E8B]'
                  } text-[#292943] placeholder-[#A3A7BE] text-sm focus:outline-none transition-colors`}
                />
                <MapPin className="w-4 h-4 text-[#686A7D] absolute left-3.5 top-3.5 pointer-events-none" />
              </div>
              {errors.location && (
                <p className="text-xs text-[#C53C53] mt-1.5 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{errors.location}</span>
                </p>
              )}
            </div>

            {/* Price & Currency */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2">
                  Currency
                </label>
                <select
                  name="currency"
                  value={formData.currency}
                  onChange={handleInputChange}
                  className="w-full px-3 py-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] text-sm focus:border-[#344E8B] focus:outline-none"
                >
                  <option value="₹">₹ (INR)</option>
                  <option value="$">$ (USD)</option>
                  <option value="AED">AED</option>
                  <option value="€">€ (EUR)</option>
                  <option value="£">£ (GBP)</option>
                </select>
              </div>

              <div className="col-span-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2">
                  Numeric Price <span className="text-[#A93478]">*</span>
                </label>
                <div className="relative">
                  <input
                    type="number"
                    name="price"
                    value={formData.price}
                    onChange={handleInputChange}
                    placeholder="8500000"
                    min="1"
                    className={`w-full pl-10 pr-4 py-3 rounded-xl bg-[#F7F7FC] border ${
                      errors.price ? 'border-[#C53C53] ring-1 ring-[#C53C53]' : 'border-[#E5E5EF] focus:border-[#344E8B]'
                    } text-[#292943] placeholder-[#A3A7BE] text-sm focus:outline-none transition-colors`}
                  />
                  <DollarSign className="w-4 h-4 text-[#686A7D] absolute left-3.5 top-3.5 pointer-events-none" />
                </div>
                {errors.price && (
                  <p className="text-xs text-[#C53C53] mt-1.5 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>{errors.price}</span>
                  </p>
                )}
              </div>
            </div>

            {/* Price Display Label */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2">
                Price Display Tag (Optional)
              </label>
              <input
                type="text"
                name="price_display"
                value={formData.price_display}
                onChange={handleInputChange}
                placeholder="e.g. ₹85 Lakh or $1.25M"
                className="w-full px-4 py-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] placeholder-[#A3A7BE] text-sm focus:border-[#344E8B] focus:outline-none transition-colors"
              />
              <p className="text-[11px] text-[#686A7D] mt-1">If blank, standard currency format is shown.</p>
            </div>

            {/* Property Type */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2 flex items-center gap-1.5">
                <Building className="w-3.5 h-3.5 text-[#344E8B]" />
                <span>Property Type</span>
              </label>
              <select
                name="property_type"
                value={formData.property_type}
                onChange={handleInputChange}
                className="w-full px-4 py-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] text-sm focus:border-[#344E8B] focus:outline-none"
              >
                <option value="apartment">Apartment / Flat</option>
                <option value="villa">Luxury Villa</option>
                <option value="independent_house">Independent House / Kothi</option>
                <option value="plot">Residential Plot / Land</option>
                <option value="commercial">Commercial Space / Office</option>
                <option value="other">Other Real Estate</option>
              </select>
            </div>

            {/* Bedrooms & Bathrooms (Conditional) */}
            {showBedBath && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2">
                    Bedrooms
                  </label>
                  <input
                    type="number"
                    name="bedrooms"
                    value={formData.bedrooms}
                    onChange={handleInputChange}
                    placeholder="2"
                    min="0"
                    max="50"
                    className="w-full px-4 py-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] text-sm focus:border-[#344E8B] focus:outline-none"
                  />
                  {errors.bedrooms && <p className="text-xs text-[#C53C53] mt-1">{errors.bedrooms}</p>}
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2">
                    Bathrooms
                  </label>
                  <input
                    type="number"
                    name="bathrooms"
                    value={formData.bathrooms}
                    onChange={handleInputChange}
                    placeholder="2"
                    min="0"
                    max="50"
                    className="w-full px-4 py-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] text-sm focus:border-[#344E8B] focus:outline-none"
                  />
                  {errors.bathrooms && <p className="text-xs text-[#C53C53] mt-1">{errors.bathrooms}</p>}
                </div>
              </div>
            )}
          </div>

          {/* Description */}
          <div className="mt-6">
            <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-[#344E8B]" />
              <span>Property Description (Optional)</span>
            </label>
            <textarea
              name="description"
              rows={3}
              value={formData.description}
              onChange={handleInputChange}
              maxLength={1500}
              placeholder="Exquisite luxury apartment featuring contemporary styling, modular fittings, and panoramic views..."
              className="w-full px-4 py-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] placeholder-[#A3A7BE] text-sm focus:border-[#344E8B] focus:outline-none resize-none transition-colors"
            />
          </div>

          {/* Key Features Chips Input */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-[#292943]">
                Key Features <span className="text-[#A93478]">*</span>
              </label>
              <span className="text-xs text-[#686A7D]">
                {formData.key_features.length}/15 features
              </span>
            </div>

            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newFeature}
                onChange={(e) => setNewFeature(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddFeature();
                  }
                }}
                placeholder="e.g. Modular Italian Kitchen, Parkland View, Covered Parking..."
                className="flex-1 px-4 py-2.5 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] placeholder-[#A3A7BE] text-sm focus:border-[#344E8B] focus:outline-none"
              />
              <button
                type="button"
                onClick={handleAddFeature}
                className="px-5 py-2.5 rounded-xl bg-[#344E8B]/10 border border-[#344E8B]/30 text-[#344E8B] hover:bg-[#344E8B]/20 font-bold text-sm flex items-center gap-1.5 cursor-pointer transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>Add</span>
              </button>
            </div>

            {errors.key_features && (
              <p className="text-xs text-[#C53C53] mb-3 flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>{errors.key_features}</span>
              </p>
            )}

            {/* Chips Container */}
            <div className="flex flex-wrap gap-2 min-h-[38px] p-2 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF]">
              {formData.key_features.length === 0 ? (
                <span className="text-xs text-[#686A7D] italic p-1">No features added yet. Type above and click Add.</span>
              ) : (
                formData.key_features.map((feat, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#344E8B]/10 border border-[#344E8B]/30 text-[#344E8B] text-xs font-semibold"
                  >
                    <span>{feat}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveFeature(idx)}
                      className="hover:text-[#A93478] transition-colors cursor-pointer"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </span>
                ))
              )}
            </div>
          </div>
        </div>

        {/* SECTION 2: IMAGE UPLOADER & REORDERING */}
        <div className="brand-card p-6 sm:p-8 bg-white border border-[#E5E5EF] shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#344E8B]/10 border border-[#344E8B]/20 flex items-center justify-center text-[#344E8B]">
                <ImageIcon className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold font-outfit text-[#292943]">Property Visuals</h3>
                <p className="text-xs text-[#686A7D]">Drag to reorder scenes. 4 to 8 images required.</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span
                className={`text-xs font-bold px-3 py-1 rounded-full border ${
                  images.length >= 4 && images.length <= 8
                    ? 'border-[#21865B]/40 bg-[#21865B]/10 text-[#21865B]'
                    : 'border-[#A93478]/40 bg-[#A93478]/10 text-[#A93478]'
                }`}
              >
                {images.length} / 8 photos ({images.length < 4 ? `Need ${4 - images.length} more` : 'Count valid'})
              </span>
            </div>
          </div>

          {/* Upload Drop Zone */}
          <div
            onDragOver={handleDropZoneOver}
            onDragLeave={handleDropZoneLeave}
            onDrop={handleDropZoneDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
              isDraggingOver
                ? 'border-[#344E8B] bg-[#344E8B]/5 scale-[1.01]'
                : 'border-[#D5D7E8] hover:border-[#344E8B]/50 bg-[#F7F7FC]'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              multiple
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(e) => {
                if (e.target.files) handleFiles(e.target.files);
              }}
            />
            <div className="flex flex-col items-center justify-center">
              <div className="w-14 h-14 rounded-2xl bg-[#344E8B]/10 border border-[#344E8B]/20 flex items-center justify-center text-[#344E8B] mb-4">
                <Upload className="w-7 h-7" />
              </div>
              <p className="text-sm font-bold text-[#292943]">
                Click to browse or drag & drop high-res property photos
              </p>
              <p className="text-xs text-[#686A7D] mt-1">
                JPEG, PNG, or WebP up to 15MB each. First photo will be the opening cover scene.
              </p>
            </div>
          </div>

          {errors.images && (
            <p className="text-xs text-[#C53C53] mt-3 flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4" />
              <span>{errors.images}</span>
            </p>
          )}

          {/* Uploaded Grid with drag reorder */}
          {images.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-3 text-xs text-[#686A7D]">
                <span>Scene Sequence (Drag handle to reposition):</span>
                <span>Scene 1 = Opening • Scene {images.length} = Closing</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                {images.map((img, index) => (
                  <div
                    key={img.image_id || index}
                    draggable
                    onDragStart={(e) => handleDragStart(e, index)}
                    onDragEnter={(e) => handleDragEnter(e, index)}
                    onDragEnd={handleDragEnd}
                    onDragOver={(e) => e.preventDefault()}
                    className={`relative rounded-xl overflow-hidden bg-white border ${
                      index === 0
                        ? 'border-[#344E8B] ring-2 ring-[#344E8B]/20'
                        : 'border-[#E5E5EF]'
                    } group select-none shadow-sm transition-all`}
                  >
                    {/* Scene Index Badge */}
                    <div className="absolute top-2 left-2 z-10 flex items-center gap-1 bg-white/90 backdrop-blur-md px-2 py-0.5 rounded text-[11px] font-bold text-[#344E8B] border border-[#E5E5EF] shadow-sm">
                      <span>#{index + 1}</span>
                      {index === 0 && <span className="text-[9px] uppercase tracking-wider text-[#A93478]">Cover</span>}
                    </div>

                    {/* Drag Handle */}
                    <div className="absolute top-2 right-9 z-10 p-1 rounded bg-white/80 text-[#686A7D] opacity-70 group-hover:opacity-100 cursor-grab active:cursor-grabbing hover:text-[#292943] shadow-sm">
                      <GripVertical className="w-3.5 h-3.5" />
                    </div>

                    {/* Remove Button */}
                    <button
                      type="button"
                      onClick={() => handleRemoveImage(img.image_id)}
                      className="absolute top-2 right-2 z-10 p-1 rounded-md bg-white/90 hover:bg-red-50 border border-red-200 text-[#C53C53] transition-colors cursor-pointer shadow-sm"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>

                    {/* Image Thumbnail */}
                    <div className="aspect-video w-full bg-slate-100 overflow-hidden relative">
                      <img
                        src={img.preview_url || `/api/images/${img.image_id}/preview`}
                        alt={img.filename || `Photo ${index + 1}`}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="%2394a3b8" stroke-width="1"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>';
                        }}
                      />

                      {/* Uploading Spinner */}
                      {img.status === 'uploading' && (
                        <div className="absolute inset-0 bg-white/80 flex flex-col items-center justify-center gap-1.5">
                          <div className="w-5 h-5 border-2 border-[#344E8B] border-t-transparent rounded-full animate-spin" />
                          <span className="text-[10px] text-[#344E8B] font-bold">Uploading...</span>
                        </div>
                      )}

                      {/* Error Overlay */}
                      {img.status === 'error' && (
                        <div className="absolute inset-0 bg-red-50/90 flex flex-col items-center justify-center p-2 text-center">
                          <AlertCircle className="w-5 h-5 text-[#C53C53] mb-1" />
                          <span className="text-[10px] text-[#C53C53] font-bold">{img.errorMessage || 'Upload failed'}</span>
                        </div>
                      )}
                    </div>

                    {/* Image Details */}
                    <div className="p-2.5 bg-white text-[11px] border-t border-[#E5E5EF]">
                      <div className="text-[#292943] truncate font-semibold">
                        {img.original_filename || img.filename || `Image_${index + 1}`}
                      </div>
                      <div className="text-[#686A7D] text-[10px] flex items-center justify-between mt-0.5">
                        <span>{formatBytes(img.size_bytes)}</span>
                        {img.status === 'success' && (
                          <span className="text-[#21865B] font-bold flex items-center gap-0.5">
                            <CheckCircle2 className="w-2.5 h-2.5" /> Ready
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* SECTION 3: VIDEO STYLING & SETTINGS */}
        <div className="brand-card p-6 sm:p-8 bg-white border border-[#E5E5EF] shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-lg bg-[#344E8B]/10 border border-[#344E8B]/20 flex items-center justify-center text-[#344E8B]">
              <Palette className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold font-outfit text-[#292943]">Visual Themes & Format</h3>
              <p className="text-xs text-[#686A7D]">Pacing, aspect ratio, audio and cinematography themes</p>
            </div>
          </div>

          {/* Theme Selection Cards */}
          <div className="mb-8">
            <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-3">
              Cinematic Theme
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {themes.map((t) => {
                const isSelected = formData.theme === t.id;
                return (
                  <div
                    key={t.id}
                    onClick={() => setFormData((p) => ({ ...p, theme: t.id }))}
                    className={`cursor-pointer rounded-xl p-4 border transition-all ${
                      isSelected
                        ? 'border-[#344E8B] ring-2 ring-[#344E8B]/20 bg-[#344E8B]/5 shadow-sm'
                        : 'border-[#E5E5EF] bg-white hover:border-[#344E8B]/40 hover:bg-[#F7F7FC]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-sm text-[#292943] font-outfit">{t.name}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        isSelected ? 'bg-[#344E8B] text-white' : 'bg-[#E5E5EF] text-[#686A7D]'
                      }`}>
                        {t.id}
                      </span>
                    </div>
                    <p className="text-xs text-[#686A7D] leading-relaxed">{t.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Duration & Aspect Ratio Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Duration */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-3 flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-[#344E8B]" />
                <span>Video Target Duration</span>
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[20, 30, 40].map((dur) => (
                  <button
                    key={dur}
                    type="button"
                    onClick={() => setFormData((p) => ({ ...p, duration: dur }))}
                    className={`py-3 px-3 rounded-xl border text-center font-bold text-sm transition-all cursor-pointer ${
                      formData.duration === dur
                        ? 'border-[#344E8B] bg-[#344E8B]/10 text-[#344E8B] shadow-sm font-bold'
                        : 'border-[#E5E5EF] bg-white text-[#686A7D] hover:border-[#344E8B]/40'
                    }`}
                  >
                    <div>{dur}s</div>
                    <span className="text-[10px] font-normal text-[#686A7D]">
                      {dur === 20 ? 'Fast Reel' : dur === 30 ? 'Standard' : 'Extended'}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Aspect Ratio */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-3 flex items-center gap-1.5">
                <Monitor className="w-4 h-4 text-[#344E8B]" />
                <span>Aspect Ratio</span>
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFormData((p) => ({ ...p, aspect_ratio: '16:9' }))}
                  className={`py-3 px-4 rounded-xl border flex items-center justify-center gap-2 font-bold text-sm transition-all cursor-pointer ${
                    formData.aspect_ratio === '16:9'
                      ? 'border-[#344E8B] bg-[#344E8B]/10 text-[#344E8B] shadow-sm'
                      : 'border-[#E5E5EF] bg-white text-[#686A7D] hover:border-[#344E8B]/40'
                  }`}
                >
                  <Monitor className="w-4 h-4" />
                  <div className="text-left">
                    <div>16:9</div>
                    <span className="text-[10px] font-normal text-[#686A7D]">Landscape HD</span>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setFormData((p) => ({ ...p, aspect_ratio: '9:16' }))}
                  className={`py-3 px-4 rounded-xl border flex items-center justify-center gap-2 font-bold text-sm transition-all cursor-pointer ${
                    formData.aspect_ratio === '9:16'
                      ? 'border-[#344E8B] bg-[#344E8B]/10 text-[#344E8B] shadow-sm'
                      : 'border-[#E5E5EF] bg-white text-[#686A7D] hover:border-[#344E8B]/40'
                  }`}
                >
                  <Smartphone className="w-4 h-4" />
                  <div className="text-left">
                    <div>9:16</div>
                    <span className="text-[10px] font-normal text-[#686A7D]">Reels / Shorts</span>
                  </div>
                </button>
              </div>
            </div>
          </div>

          {/* Narration & Music Toggles */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-[#E5E5EF]">
            <div
              onClick={() =>
                setFormData((p) => ({ ...p, narration_enabled: !p.narration_enabled }))
              }
              className={`p-4 rounded-xl border cursor-pointer flex items-center justify-between transition-all ${
                formData.narration_enabled
                  ? 'border-[#344E8B]/40 bg-[#344E8B]/5'
                  : 'border-[#E5E5EF] bg-white'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                    formData.narration_enabled
                      ? 'bg-[#344E8B]/20 text-[#344E8B]'
                      : 'bg-slate-100 text-slate-400'
                  }`}
                >
                  <Mic className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-bold text-[#292943]">Voiceover Narration</div>
                  <div className="text-xs text-[#686A7D]">Spoken scene commentary</div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={formData.narration_enabled}
                onChange={() => {}}
                className="w-4 h-4 accent-[#344E8B] cursor-pointer"
              />
            </div>

            <div
              onClick={() =>
                setFormData((p) => ({ ...p, music_enabled: !p.music_enabled }))
              }
              className={`p-4 rounded-xl border cursor-pointer flex items-center justify-between transition-all ${
                formData.music_enabled
                  ? 'border-[#344E8B]/40 bg-[#344E8B]/5'
                  : 'border-[#E5E5EF] bg-white'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                    formData.music_enabled
                      ? 'bg-[#344E8B]/20 text-[#344E8B]'
                      : 'bg-slate-100 text-slate-400'
                  }`}
                >
                  <Volume2 className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-bold text-[#292943]">Ambient Soundtrack</div>
                  <div className="text-xs text-[#686A7D]">Subtle background music bed</div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={formData.music_enabled}
                onChange={() => {}}
                className="w-4 h-4 accent-[#344E8B] cursor-pointer"
              />
            </div>
          </div>

          {/* AI Voice Modulation & Accent Selection */}
          {formData.narration_enabled && (
            <div className="mt-6 pt-6 border-t border-[#E5E5EF]">
              <div className="flex items-center justify-between mb-3">
                <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] flex items-center gap-1.5">
                  <Mic className="w-4 h-4 text-[#344E8B]" />
                  <span>AI Narrator Voice & Accent</span>
                </label>
                <span className="text-[11px] font-bold text-[#21865B] bg-[#21865B]/10 px-2.5 py-0.5 rounded">
                  Studio Neural Models
                </span>
              </div>
              <p className="text-xs text-[#686A7D] mb-4">
                Select the voice timbre, gender, and accent that best matches your target property buyers:
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {[
                  {
                    id: 'en-US-BrianNeural',
                    title: 'Executive Studio',
                    accent: 'US English • Male',
                    tone: 'Deep, warm, confident commercial narrator',
                    badge: 'Recommended',
                  },
                  {
                    id: 'en-US-AriaNeural',
                    title: 'Modern Presenter',
                    accent: 'US English • Female',
                    tone: 'Crisp, polished, engaging broadcast style',
                    badge: 'Popular',
                  },
                  {
                    id: 'en-IN-PrabhatNeural',
                    title: 'Indian Executive',
                    accent: 'Indian English • Male',
                    tone: 'Authoritative, clear, grounded business tone',
                    badge: 'Regional Best',
                  },
                  {
                    id: 'en-IN-NeerjaNeural',
                    title: 'Indian Elegance',
                    accent: 'Indian English • Female',
                    tone: 'Warm, refined, smooth luxury host',
                    badge: 'Warm & Fluent',
                  },
                  {
                    id: 'en-GB-RyanNeural',
                    title: 'British Prestige',
                    accent: 'UK English • Male',
                    tone: 'Sophisticated, formal heritage delivery',
                    badge: 'Luxury Estates',
                  },
                ].map((v) => {
                  const isSelected = (formData.voice_accent || 'en-US-BrianNeural') === v.id;
                  return (
                    <div
                      key={v.id}
                      onClick={() => setFormData((p) => ({ ...p, voice_accent: v.id }))}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'border-[#344E8B] bg-[#344E8B]/10 shadow-sm ring-1 ring-[#344E8B]/30'
                          : 'border-[#E5E5EF] bg-white hover:border-[#344E8B]/40 hover:bg-[#F7F7FC]'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="font-bold text-sm text-[#292943] font-outfit flex items-center gap-1.5">
                          <span>{v.title}</span>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isSelected ? 'bg-[#344E8B] text-white' : 'bg-slate-100 text-[#686A7D]'
                        }`}>
                          {v.badge}
                        </span>
                      </div>
                      <div className="text-[11px] font-semibold text-[#A93478] mb-1">
                        {v.accent}
                      </div>
                      <div className="text-[11px] text-[#686A7D] leading-tight">
                        {v.tone}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* SECTION 4: CALL TO ACTION & CONTACT */}
        <div className="brand-card p-6 sm:p-8 bg-white border border-[#E5E5EF] shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-lg bg-[#344E8B]/10 border border-[#344E8B]/20 flex items-center justify-center text-[#344E8B]">
              <Phone className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold font-outfit text-[#292943]">Closing Call to Action</h3>
              <p className="text-xs text-[#686A7D]">Agent branding and viewer next steps for the final scene</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2">
                Call to Action Text
              </label>
              <input
                type="text"
                name="cta_text"
                value={formData.cta_text}
                onChange={handleInputChange}
                placeholder="Schedule a Visit"
                className="w-full px-4 py-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] placeholder-[#A3A7BE] text-sm focus:border-[#344E8B] focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-[#344E8B]" />
                <span>Contact Name / Firm</span>
              </label>
              <input
                type="text"
                name="contact_name"
                value={formData.contact_name}
                onChange={handleInputChange}
                placeholder="Sales Team or Agent Name"
                className="w-full px-4 py-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] placeholder-[#A3A7BE] text-sm focus:border-[#344E8B] focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#292943] mb-2">
                Contact Details (Phone / Email)
              </label>
              <input
                type="text"
                name="contact_details"
                value={formData.contact_details}
                onChange={handleInputChange}
                placeholder="+91 98765 43210"
                className="w-full px-4 py-3 rounded-xl bg-[#F7F7FC] border border-[#E5E5EF] text-[#292943] placeholder-[#A3A7BE] text-sm focus:border-[#344E8B] focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* BOTTOM ACTIONS */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4">
          <button
            type="button"
            onClick={onBack}
            className="w-full sm:w-auto px-6 py-3.5 rounded-xl border border-[#E5E5EF] bg-white text-[#686A7D] hover:text-[#292943] hover:border-[#344E8B] font-semibold text-sm transition-colors cursor-pointer"
          >
            Cancel & Go Back
          </button>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full sm:w-auto brand-gradient-btn px-9 py-4 rounded-xl text-white font-bold text-base flex items-center justify-center gap-3 shadow-lg cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isSubmitting ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Generating Storyboard...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5 text-white" />
                <span>Review Storyboard</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
