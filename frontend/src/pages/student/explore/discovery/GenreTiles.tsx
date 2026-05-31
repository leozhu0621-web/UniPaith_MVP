import { GENRE_TILES } from './constants'

// Spec 10 §2/§11 — genre tiles for the empty state. Muted surface, no
// decorative icons (brand §13). Each drops a `major` scope chip.

interface GenreTilesProps {
  onPick: (tile: { value: string; label: string }) => void
}

export default function GenreTiles({ onPick }: GenreTilesProps) {
  return (
    <div data-testid="genre-tiles">
      <p className="text-eyebrow uppercase text-muted-foreground font-semibold mb-2">Or browse</p>
      <div className="flex flex-wrap gap-2">
        {GENRE_TILES.map(t => (
          <button
            key={t.value}
            type="button"
            onClick={() => onPick(t)}
            className="px-3 py-2 rounded-lg bg-muted border border-border text-sm text-foreground hover:border-secondary/50 hover:bg-muted/60 transition-colors"
          >
            {t.label}
          </button>
        ))}
      </div>
    </div>
  )
}
