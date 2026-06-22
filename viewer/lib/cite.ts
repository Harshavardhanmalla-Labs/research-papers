import type { Paper } from "./papers";

const REPO = "https://github.com/Harshavardhanmalla-Labs/research-papers";
const AUTHOR_BIB = "Malla, Harshavardhan";
const AUTHOR_IEEE = "H. Malla";

// Publication metadata. Papers not listed default to a 2026 preprint hosted in the repository.
type Pub = { year: string; venue?: string; volume?: string; doi?: string };
const PUB: Record<string, Pub> = {
  // Published, peer-reviewed.
  paper21: {
    year: "2024",
    venue: "Journal of Engineering Research and Sciences",
    volume: "vol. 3, no. 1",
    doi: "10.55708/js0304001",
  },
};

function citeKey(p: Paper, year: string): string {
  const slug = p.shortTitle.toLowerCase().replace(/[^a-z0-9]+/g, "");
  return `malla${year}${slug}`.slice(0, 42);
}

/** IEEE-style reference string. */
export function ieeeCitation(p: Paper): string {
  const m = PUB[p.id] ?? { year: "2026" };
  if (m.doi) {
    return `${AUTHOR_IEEE}, "${p.title}," ${m.venue}, ${m.volume}, ${m.year}, doi: ${m.doi}.`;
  }
  return `${AUTHOR_IEEE}, "${p.title}," 2026, preprint. [Online]. Available: ${REPO}/tree/main/${p.root}`;
}

/** BibTeX entry. */
export function bibtex(p: Paper): string {
  const m = PUB[p.id] ?? { year: "2026" };
  const key = citeKey(p, m.year);
  if (m.doi) {
    return [
      `@article{${key},`,
      `  author  = {${AUTHOR_BIB}},`,
      `  title   = {${p.title}},`,
      `  journal = {${m.venue}},`,
      `  volume  = {3},`,
      `  number  = {1},`,
      `  year    = {${m.year}},`,
      `  doi     = {${m.doi}}`,
      `}`,
    ].join("\n");
  }
  return [
    `@misc{${key},`,
    `  author       = {${AUTHOR_BIB}},`,
    `  title        = {${p.title}},`,
    `  year         = {2026},`,
    `  howpublished = {\\url{${REPO}/tree/main/${p.root}}},`,
    `  note         = {Preprint}`,
    `}`,
  ].join("\n");
}

export function isPublished(p: Paper): boolean {
  return !!PUB[p.id]?.doi;
}
