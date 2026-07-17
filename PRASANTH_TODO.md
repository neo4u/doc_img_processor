# PRASANTH_TODO — your manual tasks, in plain English (updated 2026-07-16)

Everything here is something only a human can do (print photos, judge how a photo
looks, click through apps). Work through the sections in any order. When you're
done, tell Claude what passed and what didn't — it remembers the context.

---

## Section 0 — One-time setup (mostly done for you)

- [x] ~~Edit the Claude Desktop config file~~ — **Claude already did this for you**
      on 2026-07-16. A backup of the old config was saved as
      `claude_desktop_config.json.bak` in the same folder.
- [ ] **Restart the Claude Desktop app** so it picks up the new config:
      1. Click on the Claude Desktop app (the macOS application, not the terminal
         and not the website).
      2. Press **⌘Q** to quit it completely. Closing the window is not enough —
         you must fully quit.
      3. Open Claude Desktop again from Spotlight or the Dock.
- [ ] **Check the connection worked:** open Settings inside Claude Desktop (press
      ⌘,) and look for a section named **Connectors** or **MCP servers**. You
      should see one called **doc-toolkit**. If you don't see it, tell Claude.
- [ ] **Install the router skill** (teaches Desktop when to use your toolkit):
      1. In Claude Desktop, open **Settings → Capabilities → Skills**.
      2. Click **Upload skill**.
      3. Pick the file **`doc-toolkit-router-skill.zip`** from your Downloads folder.
- [ ] *(Optional)* Run this once in a terminal so future git commits are linked to
      your GitHub account:
      `git config --global user.name "Prasanth Kommini" && git config --global user.email "prashanth.kommini@gmail.com"`

---

## Section 1 — Decide whether to keep headroom (takes 2 normal workdays)

**Background:** headroom is the proxy your `hclaude` command routes Claude through.
The data shows it has saved zero tokens across 3,156 requests, and it may be the
cause of the "weird results" you noticed. This experiment settles it.

- [ ] **Day 1 — work normally.** Use `hclaude` as usual. If Claude does anything
      weird (tools failing to load, strange errors), write it down.
- [ ] **Day 2 — use the test version.** Open a NEW terminal window and use
      `hclaude-bare` instead of `hclaude`. It is identical except it skips
      headroom. Again, note anything weird.
- [ ] **Compare.** If day 2 felt the same or better, and your costs look no
      different, tell Claude *"drop headroom"* — it will simplify the setup.

---

## Section 2 — Test the toolkit against the real world

These prove the toolkit works where it matters: paper, portals, and family.

- [ ] **Take a real photo.** Have a family member stand about half a meter in
      front of a plain, light-colored wall, facing a window for light. Take the
      photo at eye level from about 1.2 meters away. No glasses, neutral face.
- [ ] **Make the passport photo.** In a terminal:
      `cd ~/doc_img_processor && tools/cli.sh photo <drag the photo file here> --spec india_oci`
      You should get two new files next to the original: the photo itself and a
      4×6 print sheet. The output should be upright and under 200 KB.
- [ ] **Judge it like a consular officer.** Look at the photo: is the head roughly
      50–70% of the frame height? Neutral expression? No shadows? The tool
      guarantees size and format, but only a human can judge these — for now.
- [ ] **The Walgreens test.** Upload the file ending in `_sheet4x6.jpg` to the
      Walgreens (or CVS) photo site. Order it as a **standard 4×6 glossy print**.
      Important: if the site asks about sizing, choose **"actual size"** — never
      "fit" or "fill". When you pick it up, cut along the faint gray lines. You
      should have six correctly-sized 2×2 inch photos for about 40 cents.
- [ ] **The portal test.** Submit the OCI photo to the actual OCI portal. It
      should be accepted without size or format complaints.
- [ ] **Compress a real scan.** Take any big scanned PDF you have and run:
      `tools/cli.sh compress <the file> out.pdf --kb 1000`
      Open both files side by side. The output should be under 1 MB and the text
      and stamps should look just as sharp.
- [ ] **The most important test — your wife, no coaching.** Ask her to open a
      terminal, type `cd ~/doc_img_processor && hclaude`, drag a photo into the
      window, and type "make passport photos of this". Watch silently. Wherever
      she gets stuck is the most valuable bug report this project can get.

---

## Section 3 — Test the toolkit from Claude Desktop (after Section 0)

- [ ] In a Desktop chat, ask: *"What passport photo specs can you produce?"* —
      Claude should call a tool and list three presets.
- [ ] Ask it to compress a real file, using the full path, for example:
      *"Compress /Users/prasanthk/Downloads/somefile.pdf to under 500 KB"* —
      it should run the tool and report the before/after sizes honestly.
- [ ] **Test the three-way routing** (this checks the router skill from Section 0):
      1. *"Make an OCI photo from this photo"* → it should use the toolkit.
      2. *"Rotate this image 90 degrees"* → it should write ordinary code, NOT
         force the toolkit.
      3. *"Remove the shadow behind her head"* → it should honestly say it can't
         do that yet and give you retake instructions instead of pretending.
- [ ] **Test the honesty case:** ask it to get a 50-page scan under 200 KB — it
      should tell you that's not reachable and offer options, not silently
      produce garbage.

**Note:** the earlier warning about Desktop overwriting files is now fixed —
tools refuse to overwrite existing files unless you explicitly say so, and they
can only touch files under your home folder.

---

## When you're done

Tell Claude which boxes passed and which failed — especially the wife test
(Section 2) and the three-way routing test (Section 3). The next build work
queued after that is Wave 5 (see docs/PLAN.md).
