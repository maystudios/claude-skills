import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Menu, X } from "lucide-react";

// ADAPT: add/remove nav links to match your page sections
const navLinks = [
  { label: "Home", href: "#home", section: "home" },
  { label: "Features", href: "#features", section: "features" },
  { label: "How It Works", href: "#how-it-works", section: "how-it-works" },
  { label: "Docs", href: "#docs", section: "docs" },
];

const easeInOutCubic = (t: number) =>
  t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

function smoothScrollTo(sectionId: string, duration = 700, onDone?: () => void) {
  const target =
    sectionId === "home"
      ? 0
      : (() => {
          const el = document.getElementById(sectionId);
          if (!el) return null;
          return el.getBoundingClientRect().top + window.pageYOffset - 64;
        })();

  if (target === null) return;

  const start = window.scrollY;
  const distance = target - start;
  if (Math.abs(distance) < 2) {
    onDone?.();
    return;
  }

  const startTime = performance.now();
  const step = (now: number) => {
    const progress = Math.min((now - startTime) / duration, 1);
    window.scrollTo(0, start + distance * easeInOutCubic(progress));
    if (progress < 1) requestAnimationFrame(step);
    else onDone?.();
  };
  requestAnimationFrame(step);
}

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<string>("home");
  const isScrollingRef = useRef(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Track visible section — ignored during programmatic scroll
  useEffect(() => {
    const sectionIds = navLinks.map((l) => l.section);
    const sections = sectionIds
      .map((id) => document.getElementById(id))
      .filter(Boolean) as HTMLElement[];

    if (sections.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (isScrollingRef.current) return;
        const visible = entries.filter((e) => e.isIntersecting);
        if (visible.length === 0) return;
        const top = visible.reduce((a, b) =>
          a.intersectionRatio > b.intersectionRatio ? a : b
        );
        setActiveSection(top.target.id);
      },
      { threshold: [0.2, 0.5], rootMargin: "-64px 0px -30% 0px" }
    );

    sections.forEach((s) => observer.observe(s));
    return () => observer.disconnect();
  }, []);

  const handleNavClick = (
    e: React.MouseEvent,
    section: string,
    closeMobile = false
  ) => {
    e.preventDefault();
    if (closeMobile) setMobileOpen(false);
    setActiveSection(section);
    isScrollingRef.current = true;
    smoothScrollTo(section, 700, () => {
      isScrollingRef.current = false;
    });
  };

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 border-b ${
        scrolled
          ? "bg-background/80 backdrop-blur-lg border-border"
          : "bg-transparent border-transparent"
      }`}
    >
      <nav className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* ADAPT: replace "maxsim-flutter" with your product name */}
        <a
          href="#home"
          onClick={(e) => handleNavClick(e, "home")}
          className="text-lg font-bold tracking-tight text-foreground"
        >
          maxsim-flutter
        </a>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => {
            const active = activeSection === link.section;
            return (
              <a
                key={link.href}
                href={link.href}
                onClick={(e) => handleNavClick(e, link.section)}
                className={`relative text-sm pb-1 transition-colors duration-200 cursor-pointer ${
                  active ? "text-foreground" : "text-muted hover:text-foreground"
                }`}
              >
                {link.label}
                {active && (
                  <motion.span
                    layoutId="nav-active-dot"
                    className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 block w-1 h-1 rounded-full bg-accent"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </a>
            );
          })}
          {/* ADAPT: replace with your GitHub URL */}
          <a
            href="https://github.com/maystudios/maxsim-flutter"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm px-4 py-2 rounded-md border border-border text-foreground hover:bg-surface transition-colors"
          >
            GitHub
          </a>
        </div>

        {/* Mobile Toggle */}
        <button
          className="md:hidden text-foreground"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </nav>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-background/95 backdrop-blur-lg border-b border-border"
          >
            <div className="px-6 py-4 flex flex-col gap-4">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={(e) => handleNavClick(e, link.section, true)}
                  className={`text-sm transition-colors cursor-pointer ${
                    activeSection === link.section
                      ? "text-foreground"
                      : "text-muted hover:text-foreground"
                  }`}
                >
                  {link.label}
                </a>
              ))}
              {/* ADAPT: replace with your GitHub URL */}
              <a
                href="https://github.com/maystudios/maxsim-flutter"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-muted hover:text-foreground transition-colors"
              >
                GitHub
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
