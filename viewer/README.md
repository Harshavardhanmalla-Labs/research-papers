# Research Portal

A local web platform for viewing and reviewing the research papers in this
repository — drafts and publish-ready PDFs, side by side, per paper.

It includes:

- **Sidebar** — every paper with a live status badge (complete / drafting / packaging).
- **Manuscript view** — renders the Markdown drafts (full draft, submission draft, …).
- **PDF view** — the compiled, publish-ready PDFs.
- **Figures gallery** — all figures for the selected paper.
- **Results explorer** — the CSV result tables.
- **Artifact browser** — a file tree of the paper's repository artifacts.

> The portal is **read / review** only — it does not edit files in the browser.

---

## Quickstart

> ⚠️ This must run on **your own computer**. It serves on `localhost`, which
> only points at the machine the server is running on. (A server running in a
> cloud session is **not** reachable from your laptop's browser — there is no
> port forwarding.)

**Requirements:** [Node.js](https://nodejs.org) 18 or newer (`node -v` to check).

### One command

From this `viewer/` directory:

```bash
./start.sh
```

It installs dependencies on the first run, then starts the server. When it
prints **Ready**, open:

```
http://localhost:3333
```

### Manual (equivalent)

```bash
npm install      # first time only
npm run dev      # starts on http://localhost:3333
```

### Getting the code onto your laptop first

If you don't already have this branch locally:

```bash
git fetch origin claude/compassionate-hopper-xzwvto
git checkout claude/compassionate-hopper-xzwvto
git pull origin claude/compassionate-hopper-xzwvto
cd viewer
./start.sh
```

---

## Scripts

| Command          | What it does                                  |
| ---------------- | --------------------------------------------- |
| `./start.sh`     | Install (first run) + start the dev server.   |
| `npm run dev`    | Start the dev server on port 3333.            |
| `npm run build`  | Production build.                             |
| `npm run start`  | Serve the production build on port 3333.      |

## Troubleshooting

- **"site can't be reached" / localhost won't load** — the server is not
  running on the machine whose browser you're using. Run `./start.sh` on that
  same machine.
- **Port 3333 already in use** — stop the other process, or change the port in
  `package.json` (`next dev --port <N>`).
- **`node: command not found`** — install Node.js 18+ from https://nodejs.org.
