import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  // Safelist guarantees the per-paper accent colour classes get generated
  // even if Tailwind JIT misses them (e.g. when the class string is built
  // dynamically from PAPER_META[i]).
  safelist: [
    // backgrounds (10% opacity for active card bg, 8% for dark variant)
    "bg-sky-500/10",     "dark:bg-sky-500/8",
    "bg-teal-500/10",    "dark:bg-teal-500/8",
    "bg-violet-500/10",  "dark:bg-violet-500/8",
    "bg-rose-500/10",    "dark:bg-rose-500/8",
    "bg-amber-500/10",   "dark:bg-amber-500/8",
    "bg-emerald-500/10", "dark:bg-emerald-500/8",
    "bg-indigo-500/10",  "dark:bg-indigo-500/8",
    "bg-fuchsia-500/10", "dark:bg-fuchsia-500/8",
    "bg-lime-500/10",    "dark:bg-lime-500/8",
    "bg-red-500/10",     "dark:bg-red-500/8",
    // active-state border tints
    "border-sky-500/35",     "border-teal-500/35",
    "border-violet-500/35",  "border-rose-500/35",
    "border-amber-500/35",   "border-emerald-500/35",
    "border-indigo-500/35",  "border-fuchsia-500/35",
    "border-lime-500/35",    "border-red-500/35",
    // dot indicators
    "bg-sky-500",     "bg-teal-500",     "bg-violet-500",  "bg-rose-500",
    "bg-amber-500",   "bg-emerald-500",  "bg-indigo-500",  "bg-fuchsia-500",
    "bg-lime-500",    "bg-red-500",
    // left border (used on hover/active variant)
    "border-l-sky-500",     "border-l-teal-500",
    "border-l-violet-500",  "border-l-rose-500",
    "border-l-amber-500",   "border-l-emerald-500",
    "border-l-indigo-500",  "border-l-fuchsia-500",
    "border-l-lime-500",    "border-l-red-500",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        surface: {
          0: "rgb(var(--s0) / <alpha-value>)",
          1: "rgb(var(--s1) / <alpha-value>)",
          2: "rgb(var(--s2) / <alpha-value>)",
          3: "rgb(var(--s3) / <alpha-value>)",
          4: "rgb(var(--s4) / <alpha-value>)",
          5: "rgb(var(--s5) / <alpha-value>)",
        },
        accent: {
          DEFAULT: "rgb(var(--accent) / <alpha-value>)",
          dim:     "rgb(var(--accent-dim) / <alpha-value>)",
          muted:   "rgb(var(--accent-muted) / <alpha-value>)",
        },
        border: "rgb(var(--border-c) / <alpha-value>)",
        fg: {
          DEFAULT: "rgb(var(--fg)   / <alpha-value>)",
          2:       "rgb(var(--fg-2) / <alpha-value>)",
          3:       "rgb(var(--fg-3) / <alpha-value>)",
          4:       "rgb(var(--fg-4) / <alpha-value>)",
          5:       "rgb(var(--fg-5) / <alpha-value>)",
        },
      },
      typography: () => ({
        DEFAULT: {
          css: {
            color:      "rgb(var(--fg-2))",
            maxWidth:   "none",
            lineHeight: "1.78",
            "h1,h2,h3,h4": {
              color:         "rgb(var(--fg))",
              letterSpacing: "-0.022em",
              fontWeight:    "700",
            },
            h1: {
              fontSize:      "1.65rem",
              borderBottom:  "1px solid rgb(var(--border-c))",
              paddingBottom: "0.9rem",
              marginBottom:  "1.8rem",
            },
            h2: { fontSize: "1.28rem", marginTop: "2.6rem", marginBottom: "1rem"  },
            h3: { fontSize: "1.08rem", marginTop: "2rem",   marginBottom: "0.8rem" },
            p:  { marginTop: "1rem",   marginBottom: "1rem"  },
            a:  {
              color:          "rgb(var(--accent))",
              textDecoration: "none",
              fontWeight:     "500",
            },
            "a:hover": { textDecoration: "underline" },
            strong: { color: "rgb(var(--fg))", fontWeight: "700" },
            em:     { color: "rgb(var(--fg-2))" },
            code: {
              color:        "var(--code-color)",
              background:   "rgb(var(--s3))",
              padding:      "0.12em 0.48em",
              borderRadius: "0.35em",
              border:       "1px solid rgb(var(--border-c))",
              fontSize:     "0.80em",
              fontWeight:   "500",
            },
            "code::before": { content: '""' },
            "code::after":  { content: '""' },
            pre: {
              background:   "rgb(var(--s2))",
              border:       "1px solid rgb(var(--border-c))",
              borderRadius: "0.85rem",
              padding:      "1.3rem",
            },
            "pre code": { background: "none", border: "none", padding: "0", color: "inherit" },
            blockquote: {
              borderLeftWidth:  "3px",
              fontStyle:        "normal",
              backgroundColor:  "var(--blockquote-bg)",
              borderRadius:     "0 0.65rem 0.65rem 0",
              paddingTop:       "0.6rem",
              paddingBottom:    "0.6rem",
              paddingLeft:      "1.1rem",
              color:            "rgb(var(--fg-3))",
            },
            hr: {
              borderColor:  "rgb(var(--border-c))",
              marginTop:    "2.5rem",
              marginBottom: "2.5rem",
            },
            table:    { color: "rgb(var(--fg-2))", fontSize: "0.8rem" },
            th:       { color: "rgb(var(--fg))", fontWeight: "600", background: "var(--thead-bg)" },
            "thead tr": { borderBottomColor: "var(--thead-border)" },
            "tbody tr": { borderBottomColor: "rgb(var(--border-c))" },
            img: { borderRadius: "0.5rem", border: "1px solid rgb(var(--border-c))" },
            li:  { color: "rgb(var(--fg-2))", lineHeight: "1.78" },
            ul:  { marginTop: "0.75rem", marginBottom: "0.75rem" },
            ol:  { marginTop: "0.75rem", marginBottom: "0.75rem" },
          },
        },
      }),
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
