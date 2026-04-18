import { useState, useEffect, useRef } from 'react'
import { ArrowLeft, Bookmark, BookmarkCheck, ArrowRightLeft, MessageSquare } from 'lucide-react'

interface Props {
  images: string[]
  programName: string
  institutionName: string
  isSaved: boolean
  isComparing?: boolean
  onBack: () => void
  onSave: () => void
  onCompare?: () => void
  onAskCounselor?: () => void
}

export default function HeroBanner({
  images,
  programName,
  institutionName,
  isSaved,
  isComparing,
  onBack,
  onSave,
  onCompare,
  onAskCounselor,
}: Props) {
  const [idx, setIdx] = useState(0)
  const [paused, setPaused] = useState(false)
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    if (paused || images.length <= 1) return
    timerRef.current = window.setInterval(() => {
      setIdx(i => (i + 1) % images.length)
    }, 6000)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [paused, images.length])

  const currentImg = images[idx] || images[0]

  return (
    <div
      className="relative w-full h-56 md:h-64 rounded-2xl overflow-hidden bg-student-mist mb-6 group"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {/* Background images */}
      {images.map((img, i) => (
        <img
          key={img}
          src={img}
          alt={`${institutionName} campus`}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-700 ${
            i === idx ? 'opacity-100' : 'opacity-0'
          }`}
          onError={e => (e.currentTarget.style.display = 'none')}
        />
      ))}

      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-black/30 pointer-events-none" />

      {/* Back button */}
      <button
        onClick={onBack}
        className="absolute top-4 left-4 flex items-center gap-1.5 px-3 py-1.5 bg-white/90 backdrop-blur-sm text-student-ink text-xs font-medium rounded-full hover:bg-white transition-colors shadow-sm"
      >
        <ArrowLeft size={14} />
        Back
      </button>

      {/* Action bar */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <button
          onClick={onSave}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-all shadow-sm ${
            isSaved
              ? 'bg-student text-white'
              : 'bg-white/90 backdrop-blur-sm text-student-ink hover:bg-white'
          }`}
        >
          {isSaved ? <BookmarkCheck size={14} /> : <Bookmark size={14} />}
          {isSaved ? 'Saved' : 'Save'}
        </button>
        {onCompare && (
          <button
            onClick={onCompare}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-all shadow-sm ${
              isComparing
                ? 'bg-student text-white'
                : 'bg-white/90 backdrop-blur-sm text-student-ink hover:bg-white'
            }`}
          >
            <ArrowRightLeft size={14} />
            Compare
          </button>
        )}
        {onAskCounselor && (
          <button
            onClick={onAskCounselor}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full bg-gold/90 backdrop-blur-sm text-white hover:bg-gold transition-colors shadow-sm"
          >
            <MessageSquare size={14} />
            Ask AI
          </button>
        )}
      </div>

      {/* Caption at bottom */}
      <div className="absolute bottom-4 left-5 right-5 flex items-end justify-between">
        <div className="min-w-0">
          <p className="text-white/80 text-xs font-medium drop-shadow-sm">{institutionName}</p>
          <h2 className="text-white text-xl md:text-2xl font-bold drop-shadow-md truncate">{programName}</h2>
        </div>
        {/* Carousel dots */}
        {images.length > 1 && (
          <div className="flex items-center gap-1.5">
            {images.map((_, i) => (
              <button
                key={i}
                onClick={() => setIdx(i)}
                className={`h-1.5 rounded-full transition-all ${
                  i === idx ? 'w-6 bg-white' : 'w-1.5 bg-white/50 hover:bg-white/80'
                }`}
                aria-label={`Image ${i + 1}`}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
