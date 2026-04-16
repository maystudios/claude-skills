# Section Component Patterns

Complete implementation patterns for each landing page section.

## Navbar

```tsx
"use client"; // (only if Next.js — omit for Vite)
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Menu, X, Github } from "lucide-react";

const NAV_LINKS = [
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#tech-stack", label: "Stack" },
  { href: "#docs", label: "Docs" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", h);
    return () => window.removeEventListener("scroll", h);
  }, []);

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 border-b transition-all duration-300
      ${scrolled ? "bg-background/80 backdrop-blur-lg border-border" : "bg-transparent border-transparent"}`}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <a href="#" className="font-bold text-sm tracking-tight font-mono">YourProduct</a>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-8">
          {NAV_LINKS.map(l => (
            <a key={l.href} href={l.href}
              className="text-sm text-muted hover:text-foreground transition-colors">{l.label}</a>
          ))}
        </nav>

        {/* Actions */}
        <div className="hidden md:flex items-center gap-4">
          <a href="https://github.com/your/repo" target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-muted hover:text-foreground transition-colors">
            <Github size={16} strokeWidth={1.5} /> GitHub
          </a>
          <a href="#docs" className="px-4 py-1.5 bg-accent text-white text-sm rounded-sm hover:bg-accent-light transition-colors">
            Get Started
          </a>
        </div>

        {/* Mobile burger */}
        <button className="md:hidden text-muted hover:text-foreground" onClick={() => setOpen(v => !v)}>
          {open ? <X size={20} strokeWidth={1.5} /> : <Menu size={20} strokeWidth={1.5} />}
        </button>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden bg-background/95 backdrop-blur-lg border-b border-border md:hidden">
            <div className="px-6 py-4 flex flex-col gap-4">
              {NAV_LINKS.map(l => (
                <a key={l.href} href={l.href}
                  className="text-sm text-muted hover:text-foreground transition-colors"
                  onClick={() => setOpen(false)}>{l.label}</a>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
```

---

## Hero

Key elements: animated grid bg, eyebrow, title with rotating word, description, CTAs, terminal block.

```tsx
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ArrowRight, Copy, Check } from "lucide-react";

const WORDS = ["Scaffolding", "Architecture", "Development", "Tooling"];
const INSTALL_CMD = "npx your-tool create my-project";

function AnimatedGrid() {
  const COLS = 7, ROWS = 5;
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden>
      {Array.from({ length: COLS }).map((_, i) => (
        <motion.div key={`v${i}`}
          className="absolute top-0 bottom-0 w-px"
          style={{ left: `${(i / (COLS - 1)) * 100}%`,
                   background: "linear-gradient(to bottom, transparent, var(--color-border), transparent)" }}
          initial={{ scaleY: 0 }} animate={{ scaleY: 1 }}
          transition={{ duration: 1, delay: i * 0.06, ease: "easeOut" }} />
      ))}
      {Array.from({ length: ROWS }).map((_, i) => (
        <motion.div key={`h${i}`}
          className="absolute left-0 right-0 h-px"
          style={{ top: `${(i / (ROWS - 1)) * 100}%`,
                   background: "linear-gradient(to right, transparent, var(--color-border), transparent)" }}
          initial={{ scaleX: 0 }} animate={{ scaleX: 1 }}
          transition={{ duration: 1, delay: 0.3 + i * 0.08, ease: "easeOut" }} />
      ))}
      {/* Center glow dot */}
      <motion.div className="absolute w-2 h-2 rounded-full bg-accent"
        style={{ left: "50%", top: "50%", transform: "translate(-50%,-50%)",
                 boxShadow: "0 0 24px 4px rgba(59,130,246,0.4)" }}
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: [0, 1.4, 1], opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.7 }} />
    </div>
  );
}

export function Hero() {
  const [wordIndex, setWordIndex] = useState(0);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setWordIndex(i => (i + 1) % WORDS.length), 2200);
    return () => clearInterval(t);
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText(INSTALL_CMD);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="relative bg-background pt-32 pb-24 px-6 overflow-hidden min-h-[80vh] flex items-center">
      <AnimatedGrid />
      {/* Radial vignette */}
      <div className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(59,130,246,0.05) 0%, transparent 70%)" }}
        aria-hidden />

      <div className="relative z-10 max-w-7xl mx-auto w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Content */}
          <div className="lg:col-span-7">
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}>
              <span className="block w-6 h-px bg-accent mb-4" />
              <p className="text-xs font-mono uppercase tracking-widest text-muted mb-6">
                Developer Tool
              </p>
            </motion.div>

            <motion.h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tight mb-6"
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}>
              AI-Powered{" "}
              <span className="overflow-hidden inline-block align-bottom">
                <AnimatePresence mode="wait">
                  <motion.span key={WORDS[wordIndex]} className="inline-block text-accent"
                    initial={{ y: "110%", opacity: 0 }}
                    animate={{ y: "0%", opacity: 1 }}
                    exit={{ y: "-110%", opacity: 0 }}
                    transition={{ duration: 0.38, ease: [0.32, 0, 0.67, 0] }}>
                    {WORDS[wordIndex]}
                  </motion.span>
                </AnimatePresence>
              </span>
            </motion.h1>

            <motion.p className="text-lg md:text-xl text-muted leading-relaxed mb-8 max-w-xl"
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}>
              Your product's value proposition in 2-3 sentences.
              Focus on what it does and who it's for.
            </motion.p>

            {/* CTAs */}
            <motion.div className="flex flex-wrap gap-3 mb-10"
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}>
              <a href="#docs"
                className="flex items-center gap-2 px-5 py-2.5 bg-accent text-white text-sm font-medium rounded-sm hover:bg-accent-light transition-colors">
                Get Started <ArrowRight size={16} strokeWidth={1.5} />
              </a>
              <a href="https://github.com/your/repo" target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-2 px-5 py-2.5 border border-border text-sm font-medium rounded-sm hover:bg-surface transition-colors">
                View on GitHub
              </a>
            </motion.div>

            {/* Terminal block */}
            <motion.div className="bg-surface border border-border rounded-sm font-mono text-sm max-w-sm"
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}>
              <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-border">
                {["bg-zinc-600", "bg-zinc-600", "bg-zinc-600"].map((c, i) => (
                  <span key={i} className={`w-2.5 h-2.5 rounded-full ${c}`} />
                ))}
              </div>
              <div className="px-4 py-3 flex items-center justify-between gap-4">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-accent shrink-0">$</span>
                  <span className="text-foreground text-xs truncate">{INSTALL_CMD}</span>
                </div>
                <button onClick={handleCopy} className="shrink-0 text-muted hover:text-foreground transition-colors">
                  {copied ? <Check size={14} strokeWidth={1.5} className="text-accent" /> : <Copy size={14} strokeWidth={1.5} />}
                </button>
              </div>
            </motion.div>
          </div>

          {/* Decorative right panel (optional) */}
          <div className="hidden lg:flex lg:col-span-5 items-center justify-center">
            {/* Add a decorative element, screenshot, or 3D object here */}
            <div className="relative w-64 h-64 border border-border/40">
              <div className="absolute inset-4 border border-border/30 rotate-45" />
              <div className="absolute inset-8 border border-accent/20 rotate-45" />
              <div className="absolute inset-0 m-auto w-3 h-3 bg-accent rounded-sm rotate-45"
                style={{ boxShadow: "0 0 24px 4px rgba(59,130,246,0.5)" }} />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
```

---

## Features Section

```tsx
import { motion } from "motion/react";
import { Zap, Shield, Code2, Layers, Terminal, GitBranch } from "lucide-react";

const FEATURES = [
  { Icon: Zap, title: "Fast Setup", description: "One command to scaffold production-ready structure." },
  { Icon: Shield, title: "Best Practices", description: "Opinionated defaults following industry standards." },
  { Icon: Code2, title: "Type Safe", description: "Full TypeScript with generated types and schemas." },
  { Icon: Layers, title: "Modular", description: "Opt-in modules: auth, API, database, i18n, and more." },
  { Icon: Terminal, title: "CLI First", description: "Powerful CLI with rich output and smart prompts." },
  { Icon: GitBranch, title: "CI/CD Ready", description: "Pre-configured pipelines for GitHub Actions." },
];

const containerVariants = { hidden: {}, visible: { transition: { staggerChildren: 0.08 } } };
const cardVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } }
};

export function Features() {
  return (
    <section id="features" className="bg-background py-24 px-6 border-t border-border">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-16">
          <span className="block w-6 h-px bg-accent mb-4" />
          <p className="text-xs font-mono uppercase tracking-widest text-muted mb-3">What's included</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
            Everything you need
          </h2>
          <p className="text-muted text-lg max-w-xl">
            All the patterns, tooling, and structure to ship faster without cutting corners.
          </p>
        </div>

        {/* Grid with gap-px border trick */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-border"
          variants={containerVariants} initial="hidden"
          whileInView="visible" viewport={{ once: true, margin: "-80px" }}>
          {FEATURES.map(f => (
            <motion.div key={f.title} variants={cardVariants}
              className="bg-background p-8 group transition-shadow duration-200
                         hover:[box-shadow:inset_0_0_0_1px_#3b82f6]">
              <div className="w-10 h-10 bg-surface flex items-center justify-center mb-4">
                <f.Icon size={20} strokeWidth={1.5} className="text-accent" />
              </div>
              <h3 className="font-semibold mb-2 text-foreground">{f.title}</h3>
              <p className="text-sm text-muted leading-relaxed">{f.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
```

---

## How It Works (Timeline)

```tsx
import { motion } from "motion/react";

const STEPS = [
  { n: "01", title: "Install", description: "Install globally via npm or npx.", cmd: "npm install -g your-tool" },
  { n: "02", title: "Create", description: "Scaffold your project with optional modules.", cmd: "your-tool create my-app" },
  { n: "03", title: "Develop", description: "Run the dev server and start building.", cmd: "cd my-app && npm run dev" },
  { n: "04", title: "Ship", description: "Build and deploy with one command.", cmd: "npm run build && npm run deploy" },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-background py-24 px-6 border-t border-border">
      <div className="max-w-4xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ duration: 0.5 }} className="mb-16">
          <span className="block w-6 h-px bg-accent mb-4" />
          <p className="text-xs font-mono uppercase tracking-widest text-muted mb-3">Getting started</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight">Up and running in minutes</h2>
        </motion.div>

        <div className="relative">
          {/* Growing connector line */}
          <motion.div className="absolute left-[19px] w-px bg-accent/30"
            style={{ top: "20px" }}
            initial={{ height: 0 }}
            whileInView={{ height: "calc(100% - 40px)" }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 1.5, ease: "easeOut" }} />

          <div className="flex flex-col gap-0">
            {STEPS.map((step, i) => (
              <motion.div key={step.n}
                className="flex gap-6 pb-12 last:pb-0"
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.5, delay: i * 0.1 }}>
                {/* Circle */}
                <div className="flex flex-col items-center shrink-0">
                  <div className="w-10 h-10 rounded-full border border-border bg-background flex items-center justify-center z-10">
                    <span className="text-xs font-mono text-muted">{step.n}</span>
                  </div>
                </div>

                {/* Content */}
                <div className="pt-2 pb-4 flex-1">
                  <h3 className="font-semibold mb-1">{step.title}</h3>
                  <p className="text-sm text-muted mb-3 leading-relaxed">{step.description}</p>
                  <div className="inline-flex items-center gap-2 bg-surface border border-border px-4 py-2.5 rounded-sm font-mono text-xs">
                    <span className="text-accent">$</span>
                    <span className="text-foreground">{step.cmd}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
```

---

## Tech Stack Marquee

```tsx
import { motion } from "motion/react";

const TRACK_1 = ["React", "TypeScript", "Node.js", "PostgreSQL", "Docker", "GitHub Actions", "Tailwind CSS", "Vite"];
const TRACK_2 = ["ESLint", "Prettier", "Jest", "Playwright", "Zod", "Drizzle ORM", "tRPC", "Turbo"];

function MarqueeTrack({ items, duration }: { items: string[]; duration: number }) {
  return (
    <div className="flex items-center gap-4 overflow-hidden relative">
      <motion.div className="flex items-center gap-4 shrink-0"
        animate={{ x: ["0%", "-50%"] }}
        transition={{ duration, ease: "linear", repeat: Infinity }}>
        {[...items, ...items].map((item, i) => (
          <span key={i}
            className="px-4 py-2 border border-border bg-surface text-sm whitespace-nowrap rounded-sm text-muted">
            {item}
          </span>
        ))}
      </motion.div>
    </div>
  );
}

export function TechStack() {
  return (
    <section id="tech-stack" className="bg-background py-24 px-0 border-t border-border overflow-hidden">
      <div className="max-w-6xl mx-auto px-6 mb-12">
        <span className="block w-6 h-px bg-accent mb-4" />
        <p className="text-xs font-mono uppercase tracking-widest text-muted mb-3">Built with</p>
        <h2 className="text-4xl font-bold tracking-tight">Best-in-class tooling</h2>
      </div>

      <div className="relative flex flex-col gap-4">
        {/* Gradient fade masks */}
        <div className="pointer-events-none absolute inset-y-0 left-0 w-24 bg-gradient-to-r from-background to-transparent z-10" />
        <div className="pointer-events-none absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-background to-transparent z-10" />

        <MarqueeTrack items={TRACK_1} duration={28} />
        <MarqueeTrack items={TRACK_2} duration={34} />
      </div>
    </section>
  );
}
```

---

## Footer

```tsx
import { Github, ArrowUp } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-background border-t border-border py-8 px-6">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 text-xs text-muted font-mono">
          <span>your-tool</span>
          <span className="h-3 w-px bg-border" />
          <span>v1.0.0</span>
          <span className="h-3 w-px bg-border" />
          <span>MIT License</span>
        </div>

        <div className="flex items-center gap-4">
          <a href="https://github.com/your/repo" target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-muted hover:text-foreground transition-colors">
            <Github size={14} strokeWidth={1.5} /> GitHub
          </a>
          <span className="h-3 w-px bg-border" />
          <a href="https://npmjs.com/package/your-tool" target="_blank" rel="noopener noreferrer"
            className="text-xs text-muted hover:text-foreground transition-colors">npm</a>
          <span className="h-3 w-px bg-border" />
          <a href="#" className="flex items-center gap-1 text-xs text-muted hover:text-foreground transition-colors">
            <ArrowUp size={12} strokeWidth={1.5} /> Top
          </a>
        </div>
      </div>
    </footer>
  );
}
```
