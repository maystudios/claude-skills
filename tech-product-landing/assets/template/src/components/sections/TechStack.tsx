// ADAPT: replace with your actual tech stack
// Aim for 8–12 total items for a good marquee loop
const flutterStack = [
  { name: "Flutter" },
  { name: "Riverpod" },
  { name: "go_router" },
  { name: "freezed" },
  { name: "Clean Architecture" },
  { name: "Material 3" },
];

const cliStack = [
  { name: "TypeScript" },
  { name: "Commander.js" },
  { name: "Handlebars" },
  { name: "Zod" },
];

const allItems = [...flutterStack, ...cliStack];
// Duplicate for seamless CSS loop
const marqueeItems = [...allItems, ...allItems];

function Badge({ name }: { name: string }) {
  return (
    <div className="shrink-0 inline-flex items-center gap-2 px-4 py-2 border border-border bg-surface rounded-sm mx-3">
      <span className="w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
      <span className="font-mono text-sm text-foreground/80 whitespace-nowrap">{name}</span>
    </div>
  );
}

export function TechStack() {
  return (
    <section className="bg-background py-24 border-t border-border overflow-hidden">
      <div className="max-w-6xl mx-auto px-6 mb-12">
        {/* ADAPT: section label and subtitle */}
        <p className="text-xs uppercase tracking-widest text-muted font-medium mb-4">
          Technology
        </p>
        <h2 className="text-4xl md:text-5xl font-bold text-foreground leading-tight">
          Built With
        </h2>
        <p className="mt-4 text-muted text-lg max-w-xl">
          Carefully chosen tools for generated apps and the CLI itself.
        </p>
      </div>

      {/* ADAPT: rename labels to match your tech categories */}
      <div className="max-w-6xl mx-auto px-6 mb-6 flex flex-wrap gap-6">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono uppercase tracking-widest text-muted">
            Generated App Stack
          </span>
          <span className="h-px w-8 bg-border" />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono uppercase tracking-widest text-muted">
            CLI Toolchain
          </span>
          <span className="h-px w-8 bg-border" />
        </div>
      </div>

      {/* Row 1 — scrolls left (CSS animation, no JS) */}
      <div className="relative">
        <div className="absolute left-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-r from-background to-transparent pointer-events-none" />
        <div className="absolute right-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-l from-background to-transparent pointer-events-none" />
        <div className="marquee flex will-change-transform">
          {marqueeItems.map((item, i) => (
            <Badge key={`${item.name}-${i}`} name={item.name} />
          ))}
        </div>
      </div>

      {/* Row 2 — scrolls right */}
      <div className="relative mt-4">
        <div className="absolute left-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-r from-background to-transparent pointer-events-none" />
        <div className="absolute right-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-l from-background to-transparent pointer-events-none" />
        <div className="marquee-reverse flex will-change-transform">
          {[...marqueeItems].reverse().map((item, i) => (
            <Badge key={`rev-${item.name}-${i}`} name={item.name} />
          ))}
        </div>
      </div>
    </section>
  );
}
