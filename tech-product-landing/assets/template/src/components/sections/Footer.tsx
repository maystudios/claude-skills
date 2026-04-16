import { Github, Package, ArrowUp } from "lucide-react";
import { motion, useAnimationFrame, useMotionValue, useTransform } from "motion/react";
import { useRef } from "react";
import { cn } from "@/lib/utils";

/* ─── Moving Border Button (Aceternity UI pattern) ──────────── */
function MovingBorderButton({
  children,
  onClick,
  duration = 3000,
  className,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  duration?: number;
  className?: string;
}) {
  const rectRef = useRef<SVGRectElement>(null);
  const progress = useMotionValue(0);

  useAnimationFrame((time) => {
    if (!rectRef.current) return;
    const length = rectRef.current.getTotalLength();
    progress.set(((time % duration) / duration) * length);
  });

  const px = useTransform(progress, (v) =>
    rectRef.current ? rectRef.current.getPointAtLength(v).x : 0
  );
  const py = useTransform(progress, (v) =>
    rectRef.current ? rectRef.current.getPointAtLength(v).y : 0
  );

  return (
    <button
      onClick={onClick}
      className={cn(
        "group relative inline-flex overflow-hidden rounded-lg cursor-pointer",
        className
      )}
    >
      {/* Hidden SVG rect — provides the path for the moving dot */}
      <svg
        className="absolute inset-0 h-full w-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect
          ref={rectRef}
          fill="none"
          stroke="none"
          width="100%"
          height="100%"
          rx="8"
        />
      </svg>

      {/* Moving glow dot — only visible on hover */}
      <motion.span
        className="absolute h-20 w-20 rounded-full blur-[18px] bg-accent/60 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        style={{ x: px, y: py, translateX: "-50%", translateY: "-50%" }}
      />

      {/* Static border */}
      <span className="absolute inset-0 rounded-lg border border-border/60 group-hover:border-accent/30 transition-colors duration-300" />

      {/* Label */}
      <span className="relative flex items-center gap-2 bg-surface/40 px-5 py-2.5 text-xs font-mono text-muted group-hover:text-foreground transition-colors duration-200">
        {children}
      </span>
    </button>
  );
}

/* ─── Animated Link with slide-underline ────────────────────── */
function FooterLink({
  href,
  children,
  external,
}: {
  href: string;
  children: React.ReactNode;
  external?: boolean;
}) {
  return (
    <a
      href={href}
      target={external ? "_blank" : undefined}
      rel={external ? "noopener noreferrer" : undefined}
      className="group relative inline-flex items-center gap-2 text-sm text-muted hover:text-foreground transition-colors duration-200 w-fit"
    >
      {children}
      <span className="absolute -bottom-px left-0 h-px w-0 bg-accent group-hover:w-full transition-all duration-300 ease-out" />
    </a>
  );
}

/* ─── Data — ADAPT: update links to match your product ──────── */
const NAV_LINKS = [
  { label: "Features", href: "#features" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Docs", href: "#docs" },
];

const EXTERNAL_LINKS = [
  {
    label: "GitHub",
    href: "https://github.com/maystudios/maxsim-flutter", // ADAPT
    icon: <Github size={13} strokeWidth={1.5} />,
  },
  {
    label: "npm",
    href: "https://www.npmjs.com/package/maxsim-flutter", // ADAPT
    icon: <Package size={13} strokeWidth={1.5} />,
  },
];

/* ─── Footer ────────────────────────────────────────────────── */
export function Footer() {
  const scrollToTop = () => window.scrollTo({ top: 0, behavior: "smooth" });

  return (
    <footer className="bg-background border-t border-border">
      <div className="max-w-6xl mx-auto px-6 pt-14 pb-8">

        {/* Main 3-column grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">

          {/* Brand column */}
          <div className="md:col-span-1 flex flex-col gap-4">
            {/* ADAPT: product name */}
            <span className="font-mono font-bold tracking-tight text-foreground">
              maxsim-flutter
            </span>

            {/* ADAPT: tagline */}
            <p className="text-sm text-muted leading-relaxed max-w-xs">
              AI-powered Flutter scaffolding — from a single command to a
              production-ready Clean Architecture app.
            </p>

            <div className="flex items-center gap-3">
              {/* ADAPT: __MAXSIM_VERSION__ → your version global */}
              <span className="text-xs font-mono text-muted">v{__MAXSIM_VERSION__}</span>
              <span className="h-3 w-px bg-border" />
              <span className="text-xs font-mono text-muted uppercase tracking-widest">MIT</span>
            </div>
          </div>

          {/* Navigate */}
          <div className="flex flex-col gap-4">
            <span className="text-xs font-mono uppercase tracking-widest text-muted/40">
              Navigate
            </span>
            <nav className="flex flex-col gap-3.5">
              {NAV_LINKS.map((link) => (
                <FooterLink key={link.href} href={link.href}>
                  {link.label}
                </FooterLink>
              ))}
            </nav>
          </div>

          {/* Connect */}
          <div className="flex flex-col gap-4">
            <span className="text-xs font-mono uppercase tracking-widest text-muted/40">
              Connect
            </span>
            <nav className="flex flex-col gap-3.5">
              {EXTERNAL_LINKS.map((link) => (
                <FooterLink key={link.href} href={link.href} external>
                  {link.icon}
                  {link.label}
                </FooterLink>
              ))}
            </nav>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-border/40 pt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          {/* ADAPT: copyright and community message */}
          <p className="text-xs font-mono text-muted/40">
            © {new Date().getFullYear()} maystudios — Built with care for the
            Flutter community
          </p>
          <MovingBorderButton onClick={scrollToTop}>
            <ArrowUp size={13} strokeWidth={2} />
            Back to top
          </MovingBorderButton>
        </div>

      </div>
    </footer>
  );
}
