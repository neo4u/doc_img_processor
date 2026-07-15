# PRASANTH_TODO — manual testing & config (2026-07-15)

> Human-only acceptance tests + pending config actions. Tick as you go; report
> failures/oddities to the next Claude session (memory has full context).

## 0. One-time config (blockers for §3)

- [ ] **Desktop MCP entry** — add to `~/Library/Application Support/Claude/claude_desktop_config.json`
  (top level, next to `"preferences"`), then ⌘Q + reopen Desktop:
  ```json
  "mcpServers": {
    "doc-toolkit": { "command": "/Users/prasanthk/doc_img_processor/tools/mcp.sh", "args": [] }
  }
  ```
  (hermetic alternative: `tools/mcp-bazel.sh` — slower cold start)
- [ ] **Router skill** — Desktop Settings → Capabilities → Skills → upload
  `~/Downloads/doc-toolkit-router-skill.zip` (rebuildable: `cd skills && zip -r ~/Downloads/doc-toolkit-router-skill.zip doc-toolkit-router`)
- [ ] *(optional)* git author: `git config --global user.name "Prasanth Kommini" && git config --global user.email "prashanth.kommini@gmail.com"` — links future commits to neo4u

## 1. Headroom A/B (~2 days → keep-or-drop decision)

- [ ] `headroom doctor` → expect **0 failures**
- [ ] Day 1 `hclaude`: inside session `! env | grep ANTHROPIC_BASE_URL` → expect `127.0.0.1:8787`
- [ ] Day 2 `hclaude-bare` (new terminal): same check → expect **empty** (direct)
- [ ] Both days: note tool-loading failures / weirdness / latency (hypothesis: only day 1)
- [ ] Verdict: `headroom savings` still "No savings recorded" **and** no cost delta
      → drop the wrap (edit `hclaude` to `claude --1m`), keep rtk
      Context: 3,156 proxied requests, 0 compression savings, memory unused; the
      $711 "cache savings" is native Claude Code caching re-attributed.

## 2. Toolkit — physical-world acceptance

- [ ] Real HEIC (plain wall, window light): `tools/cli.sh photo ~/path/IMG.HEIC --spec india_oci`
      → upright, 600×600, ≤200 KB
- [ ] Human compliance check vs `PRESETS['india_oci'].notes` (head %, expression — tool can't judge this until W7)
- [ ] **Walgreens loop:** upload `…_sheet4x6.jpg` as standard 4×6 glossy, "actual size"
      (never fit/fill), print, cut on gray lines → six correct 2×2" photos
- [ ] **OCI portal:** submit the photo → accepted
- [ ] `tools/cli.sh compress <big-scan>.pdf out.pdf --kb 1000` → under target, text/stamps look clean side-by-side
- [ ] `tools/cli.sh lossless <any>.jpg` → visually identical (it's bit-identical)
- [ ] **Wife UX (no coaching):** she runs `hclaude` in this repo, drags a photo,
      says "make passport photos of this" → correct output, zero flags asked.
      *Note where she stumbles — that's the highest-value bug report.*
- [ ] Any trivial commit → pre-commit hook runs gate + auto-refreshes graphify-out

## 3. Desktop / cowork MCP (after §0)

- [ ] Desktop chat: "what photo specs can you produce?" → `list_photo_specs` fires
- [ ] Full-path ask: "compress /Users/prasanthk/Downloads/x.pdf under 500 KB" → honest before→after
- [ ] Cowork session on a **different** folder, same ask → connector still reachable
- [ ] **Router 3-probe:** (a) "make an OCI photo from this" → TOOL ·
      (b) "rotate this image 90°" → ad-hoc CODE, no forced tool ·
      (c) "remove the shadow behind her head" → **HUMAN instructions** (retake guidance,
      "background replacement not shipped"), no faked capability
- [ ] Honesty probe: "50-page scan under 200 KB" → plain "unreachable" + options, no silent degradation

⚠ **Standing caution:** Wave 3 (path confinement / no-clobber) not built — Desktop-wide
tools overwrite explicit `out_path` without asking. Your testing: fine. Unsupervised
wife-from-Desktop: wait for Wave 3. (Repo-scoped `hclaude` + skills already safe.)

## When done

Tell the next session the results — especially §2 wife-UX and §3 router-probe
outcomes. Next build work queued: **Wave 3** (docs/PLAN.md).
