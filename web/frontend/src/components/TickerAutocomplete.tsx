import { useCallback, useEffect, useRef, useState } from "react";
import { Instruments, type InstrumentSuggestion } from "../api";

const DEBOUNCE_MS = 280;

type Props = {
  value: string;
  onChange: (ticker: string) => void;
  className?: string;
  placeholder?: string;
};

export function TickerAutocomplete({ value, onChange, className = "", placeholder = "Ticker" }: Props) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<InstrumentSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  const runSearch = useCallback((q: string) => {
    const t = q.trim();
    if (t.length < 1) {
      setItems([]);
      return;
    }
    setLoading(true);
    Instruments.autocomplete(t, 35)
      .then((r) => setItems(r.suggestions ?? []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    const t = value.trim();
    if (t.length < 1) {
      setItems([]);
      return;
    }
    timerRef.current = setTimeout(() => runSearch(t), DEBOUNCE_MS);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [value, runSearch]);

  useEffect(() => {
    function onDocDown(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocDown);
    return () => document.removeEventListener("mousedown", onDocDown);
  }, []);

  const showPanel = open && (loading || items.length > 0);

  return (
    <div ref={wrapRef} className={`relative ${className}`}>
      <input
        className="w-full rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm text-zinc-200"
        placeholder={placeholder}
        value={value}
        autoComplete="off"
        spellCheck={false}
        aria-autocomplete="list"
        aria-expanded={showPanel}
        onChange={(e) => {
          onChange(e.target.value.toUpperCase());
          setOpen(true);
        }}
        onFocus={() => {
          if (value.trim().length > 0) setOpen(true);
        }}
      />
      {showPanel && (
        <ul
          className="absolute z-50 mt-1 max-h-64 min-w-full w-max max-w-[min(100vw-2rem,32rem)] overflow-y-auto rounded-md border border-zinc-700 bg-zinc-950 py-1 text-left text-xs shadow-xl"
          role="listbox"
        >
          {loading && (
            <li className="px-3 py-2 font-mono text-zinc-500" role="presentation">
              Szukam…
            </li>
          )}
          {!loading &&
            items.map((it) => (
              <li key={it.symbol} role="option">
                <button
                  type="button"
                  className="flex w-full flex-col items-start gap-0.5 px-3 py-2 text-left font-mono hover:bg-zinc-800 text-zinc-200 border-0 bg-transparent cursor-pointer"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => {
                    onChange(it.symbol);
                    setOpen(false);
                  }}
                >
                  <span className="text-mint shrink-0">{it.symbol}</span>
                  <span className="text-[11px] text-zinc-500 whitespace-normal break-words">{it.name}</span>
                </button>
              </li>
            ))}
        </ul>
      )}
      <p className="mt-1 text-[10px] text-zinc-600 font-mono">
        Lista z NASDAQ Trader — dopasowanie po symbolu lub nazwie spółki.
      </p>
    </div>
  );
}
