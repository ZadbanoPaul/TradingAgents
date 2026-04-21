"""Callback LangChain: LLM + narzędzia, artefakty JSON, tokeny, koszt USD."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Callable, List, Optional

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

from web.backend.llm_pricing import estimate_usd

log = logging.getLogger(__name__)


def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()


def _message_to_text(m: BaseMessage) -> str:
    c = getattr(m, "content", "")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for block in c:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return "\n".join(parts)
    return str(c)


def _role_of(m: BaseMessage) -> str:
    t = m.__class__.__name__.replace("Message", "").lower()
    if t in ("human", "user"):
        return "user"
    if t in ("ai", "assistant"):
        return "assistant"
    if t == "system":
        return "system"
    return t


def _count_content_blocks(m: BaseMessage) -> int:
    c = getattr(m, "content", None)
    if isinstance(c, list):
        return len(c)
    return 1 if c else 0


def _serialize_messages(messages: List[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in messages:
        if not isinstance(m, BaseMessage):
            out.append({"role": "unknown", "chars": len(str(m)), "sha256": _sha256_text(str(m)), "blocks": 1})
            continue
        text = _message_to_text(m)
        out.append(
            {
                "role": _role_of(m),
                "chars": len(text),
                "sha256": _sha256_text(text),
                "blocks": _count_content_blocks(m),
                "preview": text[:12_000] + ("…" if len(text) > 12_000 else ""),
            }
        )
    return out


def _try_parse_table_and_series(text: str) -> dict[str, Any]:
    """Fallback CSV (stare odpowiedzi narzędzi)."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if len(lines) < 2:
        return {"tables": [], "series": [], "chart_sets": []}
    header = [h.strip() for h in lines[0].split(",")]
    if len(header) < 2:
        return {"tables": [], "series": [], "chart_sets": []}
    rows: list[list[str]] = []
    series: list[dict[str, Any]] = []
    for ln in lines[1:121]:
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) < 2:
            continue
        rows.append(parts)
        try:
            y = float(parts[1].replace(",", ""))
            series.append({"x": parts[0][:48], "y": y})
        except ValueError:
            continue
    return {
        "tables": [{"headers": header, "rows": rows[:60]}],
        "series": series[:100],
        "chart_sets": [],
    }


def _line_y_keys(sample: dict[str, Any]) -> list[str]:
    skip = {"date", "Date", "datetime", "t", "T"}
    keys: list[str] = []
    for k, v in sample.items():
        if k in skip:
            continue
        if isinstance(v, (int, float)):
            keys.append(k)
    return keys[:8]


def _chart_hint_from_tool_json(out: str, tool_name: str) -> dict[str, Any]:
    """Parsuje jeden lub wiele bloków JSON z narzędzi get_* (schema version 1)."""
    chart_sets: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    legacy_series: list[dict[str, Any]] = []
    raw = out or ""
    chunks = re.split(r"\n\s*\n", raw.strip())
    if len(chunks) == 1 and not raw.strip().startswith("{"):
        chunks = [raw.strip()]
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk.startswith("{"):
            continue
        try:
            data = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        tname = str(data.get("tool") or tool_name or "tool")
        pres = data.get("presentation")
        if pres == "financial_period_columns":
            cols = list(data.get("period_columns") or [])
            rows_data = data.get("metric_rows") or []
            if cols and rows_data:
                headers = ["metric"] + cols
                tb_rows: list[list[str]] = []
                for mr in rows_data[:120]:
                    if not isinstance(mr, dict):
                        continue
                    m = str(mr.get("metric", ""))
                    vals = mr.get("values") or {}
                    if not isinstance(vals, dict):
                        continue
                    tb_rows.append([m] + [str(vals.get(c, "")) for c in cols])
                if tb_rows:
                    tables.append({"headers": headers, "rows": tb_rows})
        ts = data.get("timeseries")
        if isinstance(ts, list) and ts and isinstance(ts[0], dict):
            row0 = ts[0]
            x_key = "date" if "date" in row0 else ("t" if "t" in row0 else next(iter(row0.keys())))
            y_keys = _line_y_keys(row0)
            if y_keys:
                chart_sets.append(
                    {
                        "kind": "line",
                        "title": f"{tname} · {data.get('meta', {}).get('indicator', '')}".strip(" ·"),
                        "xKey": x_key,
                        "yKeys": y_keys,
                        "rows": ts[:500],
                    }
                )
            else:
                tables.append(
                    {
                        "headers": list(row0.keys()),
                        "rows": [[str(row.get(h, "")) for h in row0.keys()] for row in ts[:80]],
                    }
                )
        kv = data.get("kv")
        if isinstance(kv, list) and kv:
            bars = []
            for e in kv:
                if not isinstance(e, dict):
                    continue
                lab = e.get("label")
                val = e.get("value")
                if lab is not None and isinstance(val, (int, float)):
                    bars.append({"name": str(lab)[:64], "value": float(val)})
            if bars:
                chart_sets.append(
                    {
                        "kind": "bar",
                        "title": f"{tname} (metryki)",
                        "bars": bars[:48],
                    }
                )
            tab_row = [[str(e.get("label", "")), str(e.get("raw", ""))] for e in kv if isinstance(e, dict)]
            if tab_row:
                tables.append({"headers": ["Pole", "Wartość"], "rows": tab_row[:120]})
        arts = data.get("articles")
        if isinstance(arts, list) and arts:
            chart_sets.append(
                {
                    "kind": "articles",
                    "title": f"{tname} · artykuły ({len(arts)})",
                    "articles": arts[:50],
                }
            )
            pub_counts: dict[str, int] = {}
            for a in arts:
                if not isinstance(a, dict):
                    continue
                p = str(a.get("publisher") or "unknown")[:40]
                pub_counts[p] = pub_counts.get(p, 0) + 1
            if pub_counts:
                chart_sets.append(
                    {
                        "kind": "bar",
                        "title": "Liczba artykułów wg źródła",
                        "bars": [{"name": k, "value": float(v)} for k, v in sorted(pub_counts.items(), key=lambda x: -x[1])[:20]],
                    }
                )
    legacy = _try_parse_table_and_series(raw)
    legacy_series = list(legacy.get("series") or [])
    if not chart_sets and legacy_series:
        chart_sets.append(
            {
                "kind": "line",
                "title": "CSV (legacy)",
                "xKey": "x",
                "yKeys": ["y"],
                "rows": [{"x": s.get("x"), "y": s.get("y")} for s in legacy_series],
            }
        )
    return {
        "chart_sets": chart_sets,
        "tables": tables + list(legacy.get("tables") or []),
        "series": legacy_series,
    }


class TransparencyCallbackHandler(BaseCallbackHandler):
    """Zbiera wywołania chat modelu i narzędzi; pełna treść w plikach pod data_dir/jobs/{id}/artifacts/."""

    def __init__(
        self,
        job_id: int,
        data_dir: str,
        quick_model: str,
        deep_model: str,
        reasoning_effort: Optional[str],
        emit: Callable[[dict[str, Any]], None],
    ) -> None:
        super().__init__()
        self._job_id = job_id
        self._data_dir = Path(data_dir)
        self._quick_model = quick_model
        self._deep_model = deep_model
        self._reasoning = reasoning_effort
        self._emit = emit
        self._seq = 0
        self._last_model: str = ""
        self._artifact_root = self._data_dir / "jobs" / str(job_id) / "artifacts"
        self._artifact_root.mkdir(parents=True, exist_ok=True)

    def _next_path(self, kind: str) -> Path:
        self._seq += 1
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", kind)[:48]
        return self._artifact_root / f"{self._seq:05d}_{safe}.json"

    def _rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self._data_dir))
        except ValueError:
            return str(path)

    def _write_artifact(self, kind: str, payload: dict[str, Any]) -> str:
        p = self._next_path(kind)
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return self._rel(p)

    def _classify_model(self, model_name: str) -> str:
        m = (model_name or "").strip()
        if m == self._deep_model:
            return "deep"
        if m == self._quick_model:
            return "quick"
        return "other"

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """Pomijamy duplikat z ChatOpenAI — szczegóły są w on_chat_model_start."""
        return

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any,
    ) -> None:
        try:
            batches = messages or []
            flat: list[BaseMessage] = []
            for group in batches:
                for m in group or []:
                    if isinstance(m, BaseMessage):
                        flat.append(m)
            joined = "\n\n---MESSAGE---\n\n".join(_message_to_text(m) for m in flat)
            batch_count = len(batches)
            content_chunks = sum(_count_content_blocks(m) for m in flat)
            kw = serialized.get("kwargs") or {}
            model = str(kw.get("model_name") or kw.get("model") or "unknown")
            self._last_model = model
            artifact = self._write_artifact(
                "llm_request",
                {
                    "type": "llm_request",
                    "job_id": self._job_id,
                    "model": model,
                    "model_role": self._classify_model(model),
                    "openai_reasoning_effort": self._reasoning,
                    "message_count": len(flat),
                    "llm_message_batches": batch_count,
                    "content_blocks_total": content_chunks,
                    "content_chunks_note": (
                        "Liczba chunków = suma bloków treści we wszystkich wiadomościach "
                        "(multimodal / structured content); partie wywołania = llm_message_batches."
                    ),
                    "total_chars": len(joined),
                    "joined_sha256": _sha256_text(joined),
                    "context_how_built": (
                        "Wiadomości BaseMessage przekazane do modelu w kolejności wywołania LangChain; "
                        "pełna treść w pliku — bez przycinania (weryfikacja: sha256 vs plik)."
                    ),
                    "messages_full": [
                        {"role": _role_of(m), "content": _message_to_text(m)} for m in flat
                    ],
                },
            )
            self._emit(
                {
                    "type": "llm",
                    "subtype": "request",
                    "title": f"LLM · request · `{model}` ({self._classify_model(model)})",
                    "model": model,
                    "model_role": self._classify_model(model),
                    "openai_reasoning_effort": self._reasoning,
                    "message_count": len(flat),
                    "llm_message_batches": batch_count,
                    "content_blocks_total": content_chunks,
                    "content_chunks_note": (
                        "Chunki = bloki content w wiadomościach; pełny tekst w pliku artefaktu "
                        "(bez przycinania — porównaj sha256 z podglądem)."
                    ),
                    "total_chars": len(joined),
                    "joined_sha256": _sha256_text(joined),
                    "artifact": artifact,
                    "artifact_download_path": f"/api/jobs/{self._job_id}/artifacts/download",
                    "prompt_editor_url": "/prompts",
                    "context_how_built": (
                        "Wiadomości BaseMessage przekazane do modelu w kolejności wywołania LangChain; "
                        "pełna treść w pliku — bez przycinania (weryfikacja: sha256 vs plik)."
                    ),
                    "messages_summary": _serialize_messages(flat),
                    "transparency_note": (
                        "Bloki treści (content blocks) — liczba jak zwrócił provider; "
                        "pełny prompt w artefakcie JSON."
                    ),
                }
            )
        except Exception:
            log.exception("transparency on_chat_model_start")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        try:
            gen = response.generations[0][0] if response.generations else None
            msg = getattr(gen, "message", None) if gen else None
            usage = None
            if msg is not None and hasattr(msg, "usage_metadata") and msg.usage_metadata:
                usage = dict(msg.usage_metadata)
            inp = int((usage or {}).get("input_tokens", 0) or 0)
            out = int((usage or {}).get("output_tokens", 0) or 0)
            tot = int((usage or {}).get("total_tokens", inp + out) or (inp + out))
            model = self._last_model or (
                str((response.llm_output or {}).get("model_name", "")) or None
            )
            usd = estimate_usd(model or "gpt-4o", inp, out) if (inp or out) else 0.0
            text_out = ""
            blocks_out = 0
            if isinstance(msg, BaseMessage):
                text_out = _message_to_text(msg)
                blocks_out = _count_content_blocks(msg)
            elif msg is not None:
                text_out = str(getattr(msg, "content", msg))
                blocks_out = 1
            artifact = self._write_artifact(
                "llm_response",
                {
                    "type": "llm_response",
                    "usage": usage,
                    "model": model,
                    "output_chars": len(text_out),
                    "output_sha256": _sha256_text(text_out),
                    "output_blocks": blocks_out,
                    "output_full": text_out,
                },
            )
            self._emit(
                {
                    "type": "llm",
                    "subtype": "response",
                    "title": "LLM · odpowiedź + tokeny + koszt",
                    "model": model,
                    "usage": {
                        "input_tokens": inp,
                        "output_tokens": out,
                        "total_tokens": tot,
                    },
                    "estimated_usd": round(usd, 6),
                    "output_chars": len(text_out),
                    "output_sha256": _sha256_text(text_out),
                    "output_blocks": blocks_out,
                    "artifact": artifact,
                    "artifact_download_path": f"/api/jobs/{self._job_id}/artifacts/download",
                    "response_preview": text_out[:32_000]
                    + ("…" if len(text_out) > 32_000 else ""),
                }
            )
        except Exception:
            log.exception("transparency on_llm_end")

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        try:
            name = (serialized or {}).get("name") or (serialized or {}).get("id") or "tool"
            artifact = self._write_artifact(
                f"tool_in_{str(name)[:30]}",
                {
                    "type": "tool_start",
                    "tool_name": name,
                    "input_chars": len(input_str or ""),
                    "input_sha256": _sha256_text(input_str or ""),
                    "input_full": input_str or "",
                },
            )
            self._emit(
                {
                    "type": "tool",
                    "subtype": "start",
                    "title": f"Narzędzie · start · {name}",
                    "tool_name": name,
                    "input_chars": len(input_str or ""),
                    "input_sha256": _sha256_text(input_str or ""),
                    "artifact": artifact,
                    "artifact_download_path": f"/api/jobs/{self._job_id}/artifacts/download",
                    "input_preview": (input_str or "")[:600]
                    + ("…" if len(input_str or "") > 600 else ""),
                }
            )
        except Exception:
            log.exception("transparency on_tool_start")

    def on_tool_end(self, output: Any = None, **kwargs: Any) -> None:
        try:
            name = kwargs.get("name") or kwargs.get("tool_name") or "tool"
            if hasattr(output, "content"):
                out = str(output.content)
            else:
                out = output if isinstance(output, str) else str(output)
            artifact = self._write_artifact(
                f"tool_out_{str(name)[:28]}",
                {
                    "type": "tool_end",
                    "tool_name": name,
                    "output_chars": len(out),
                    "output_sha256": _sha256_text(out),
                    "output_full": out,
                },
            )
            parsed = _chart_hint_from_tool_json(out, str(name))
            self._emit(
                {
                    "type": "tool",
                    "subtype": "result",
                    "title": f"Narzędzie · wynik · {name}",
                    "tool_name": name,
                    "output_chars": len(out),
                    "output_sha256": _sha256_text(out),
                    "artifact": artifact,
                    "artifact_download_path": f"/api/jobs/{self._job_id}/artifacts/download",
                    "output_preview": out[:800] + ("…" if len(out) > 800 else ""),
                    "chart_hint": parsed,
                }
            )
        except Exception:
            log.exception("transparency on_tool_end")
