import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { cn } from "@/lib/utils";

// ADAPT: 4–5 power words that describe your product's core value
const FLIP_WORDS = ["Scaffolding", "Architecture", "Development", "Tooling"];

function AnimatedGridBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden>
      {/* Fixed 100×100 px square grid — consistent on all viewports */}
      <motion.div
        className="absolute inset-0"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.2, ease: "easeOut" }}
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(39,39,42,0.5) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(39,39,42,0.4) 1px, transparent 1px)
          `,
          backgroundSize: "100px 100px",
        }}
      />
      {/* Subtle radial gradient vignette */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(59,130,246,0.05) 0%, transparent 70%)",
        }}
      />
    </div>
  );
}

function WordFlipper() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setIndex((prev) => (prev + 1) % FLIP_WORDS.length);
    }, 2200);
    return () => clearInterval(id);
  }, []);

  return (
    <span className="relative inline-flex overflow-hidden" style={{ minWidth: "10ch" }}>
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={FLIP_WORDS[index]}
          className="text-accent inline-block"
          initial={{ y: "110%", opacity: 0 }}
          animate={{ y: "0%", opacity: 1 }}
          exit={{ y: "-110%", opacity: 0 }}
          transition={{ duration: 0.38, ease: [0.32, 0, 0.67, 0] }}
        >
          {FLIP_WORDS[index]}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}

function TerminalBlock() {
  const [copied, setCopied] = useState(false);

  // ADAPT: replace with your actual install/create command
  const command = "npx maxsim-flutter create my_app";

  const handleCopy = () => {
    navigator.clipboard.writeText(command).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  };

  return (
    <motion.div
      className="w-full max-w-xl mx-auto lg:mx-0 rounded-lg overflow-hidden border border-border bg-surface"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.9 }}
    >
      {/* Terminal title bar */}
      <div className="flex items-center gap-2 px-4 py-2.5 bg-surface-light border-b border-border">
        <span className="w-3 h-3 rounded-full bg-zinc-600" />
        <span className="w-3 h-3 rounded-full bg-zinc-600" />
        <span className="w-3 h-3 rounded-full bg-zinc-600" />
        <span className="ml-2 text-xs text-muted font-mono tracking-wide">terminal</span>
      </div>
      {/* Command line */}
      <div className="flex items-center justify-between px-5 py-4 gap-4">
        <pre className="font-mono text-sm md:text-base text-foreground/90 select-all whitespace-nowrap overflow-x-auto">
          <span className="text-accent mr-2 select-none">$</span>
          <span>{command}</span>
        </pre>
        <button
          onClick={handleCopy}
          aria-label="Copy command"
          className={cn(
            "shrink-0 text-xs font-mono px-2.5 py-1 rounded border transition-colors duration-200",
            copied
              ? "border-accent/60 text-accent bg-accent/10"
              : "border-border text-muted hover:border-accent/50 hover:text-foreground"
          )}
        >
          {copied ? "copied!" : "copy"}
        </button>
      </div>
    </motion.div>
  );
}

export default function Hero() {
  return (
    <section id="home" className="relative min-h-screen flex items-center bg-background overflow-hidden">
      <AnimatedGridBackground />

      {/* Top accent rule */}
      <motion.div
        className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent/50 to-transparent"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 1, ease: "easeOut" }}
      />

      <div className="relative w-full max-w-7xl mx-auto px-6 sm:px-10 lg:px-16 py-24 lg:py-32">
        {/* Grid layout: two columns on lg+ */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">

          {/* Left column – content */}
          <div className="lg:col-span-7 flex flex-col gap-8">

            {/* Eyebrow label */}
            <motion.div
              className="flex items-center gap-3"
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <span className="block w-6 h-px bg-accent" />
              {/* ADAPT: your product category, e.g. "SaaS", "Developer Tool", "CLI" */}
              <span className="text-xs font-mono uppercase tracking-widest text-accent">
                CLI Tool
              </span>
            </motion.div>

            {/* Main heading */}
            <motion.div
              className="flex flex-col gap-2"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              {/* ADAPT: replace with your product name */}
              <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-foreground leading-none">
                maxsim-flutter
              </h1>
              {/* ADAPT: replace prefix text and FLIP_WORDS array */}
              <p className="text-xl sm:text-2xl md:text-3xl font-semibold text-muted leading-tight mt-2">
                AI-Powered Flutter{" "}
                <WordFlipper />
              </p>
            </motion.div>

            {/* Description — ADAPT: your product value proposition */}
            <motion.p
              className="max-w-lg text-base md:text-lg text-muted leading-relaxed"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.45 }}
            >
              Generate production-ready Flutter apps with Clean Architecture,
              Riverpod, and AI-assisted development &mdash; all from a single
              command.
            </motion.p>

            {/* CTA buttons */}
            <motion.div
              className="flex flex-wrap items-center gap-4"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              <a
                href="#docs"
                className="inline-flex items-center justify-center px-6 py-3 rounded-md bg-accent text-white font-semibold text-sm tracking-wide hover:bg-accent-light transition-colors duration-200"
              >
                Get Started
              </a>
              {/* ADAPT: replace with your GitHub URL */}
              <a
                href="https://github.com/maystudios/maxsim-flutter"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-md border border-border text-foreground font-semibold text-sm tracking-wide hover:border-accent/60 hover:text-accent transition-colors duration-200"
              >
                GitHub
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  aria-hidden="true"
                  className="translate-y-px"
                >
                  <path
                    d="M2 7h10M7 2l5 5-5 5"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </a>
            </motion.div>

            {/* Terminal block */}
            <TerminalBlock />
          </div>

          {/* Right column – decorative Swiss grid accent */}
          <div className="hidden lg:flex lg:col-span-5 items-center justify-center">
            <motion.div
              className="relative w-72 h-72"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              {/* Outer square */}
              <motion.div
                className="absolute inset-0 border border-border/60 rounded-sm"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.6 }}
              />
              {/* Inner square – rotated */}
              <motion.div
                className="absolute inset-8 border border-accent/30 rounded-sm"
                initial={{ rotate: 0, opacity: 0 }}
                animate={{ rotate: 45, opacity: 1 }}
                transition={{ duration: 1, delay: 0.8, ease: "easeOut" }}
              />
              {/* Center dot */}
              <motion.div
                className="absolute inset-0 flex items-center justify-center"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.5, delay: 1.1, type: "spring", stiffness: 200 }}
              >
                <div className="w-4 h-4 rounded-full bg-accent shadow-[0_0_24px_4px_rgba(59,130,246,0.4)]" />
              </motion.div>
              {/* Corner accents */}
              {[
                "top-0 left-0",
                "top-0 right-0",
                "bottom-0 left-0",
                "bottom-0 right-0",
              ].map((pos, i) => (
                <motion.div
                  key={pos}
                  className={cn("absolute w-2.5 h-2.5 border-accent/80", pos, {
                    "border-t border-l": i === 0,
                    "border-t border-r": i === 1,
                    "border-b border-l": i === 2,
                    "border-b border-r": i === 3,
                  })}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3, delay: 1.0 + i * 0.08 }}
                />
              ))}
              {/* Floating version label — uses __MAXSIM_VERSION__ Vite define */}
              {/* ADAPT: rename __MAXSIM_VERSION__ to your product's version global */}
              <motion.span
                className="absolute -bottom-8 left-0 right-0 text-center text-xs font-mono text-muted tracking-widest uppercase"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 1.4 }}
              >
                v{__MAXSIM_VERSION__}
              </motion.span>
            </motion.div>
          </div>

        </div>
      </div>

      {/* Bottom accent rule */}
      <motion.div
        className="absolute bottom-0 left-0 right-0 h-px bg-border/50"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 1, delay: 0.5, ease: "easeOut" }}
      />
    </section>
  );
}
