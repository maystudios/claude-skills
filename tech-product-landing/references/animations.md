# Framer Motion Animation Patterns

All patterns use `motion/react` (not `framer-motion` directly).

## Page Load Entrance

Standard entrance for hero elements:
```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}>
```

Stagger delays for sequential elements (0.1s apart):
```tsx
// Eyebrow: delay 0.1
// Heading: delay 0.2
// Description: delay 0.3
// CTAs: delay 0.4
// Terminal: delay 0.5
```

## Scroll-triggered (whileInView)

```tsx
<motion.div
  initial={{ opacity: 0, y: 24 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, margin: "-80px" }}
  transition={{ duration: 0.5, ease: "easeOut" }}>
```

## Stagger Container (Features Grid)

```tsx
const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } }
};
const cardVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } }
};

<motion.div variants={containerVariants} initial="hidden" whileInView="visible"
  viewport={{ once: true, margin: "-80px" }}>
  {items.map(item => (
    <motion.div key={item.id} variants={cardVariants}>...</motion.div>
  ))}
</motion.div>
```

## Hero Animated Grid Background

```tsx
// Vertical lines
{Array.from({ length: COLS }).map((_, i) => (
  <motion.div key={i}
    className="absolute top-0 bottom-0 w-px"
    style={{ left: `${(i / (COLS - 1)) * 100}%`,
             background: "linear-gradient(to bottom, transparent, var(--color-border), transparent)" }}
    initial={{ scaleY: 0 }}
    animate={{ scaleY: 1 }}
    transition={{ duration: 1, delay: i * 0.05, ease: "easeOut" }} />
))}

// Horizontal lines
{Array.from({ length: ROWS }).map((_, i) => (
  <motion.div key={i}
    className="absolute left-0 right-0 h-px"
    style={{ top: `${(i / (ROWS - 1)) * 100}%`,
             background: "linear-gradient(to right, transparent, var(--color-border), transparent)" }}
    initial={{ scaleX: 0 }}
    animate={{ scaleX: 1 }}
    transition={{ duration: 1, delay: i * 0.08, ease: "easeOut" }} />
))}

// Center accent dot with glow
<motion.div
  className="absolute w-2 h-2 rounded-full bg-accent"
  style={{
    left: "50%", top: "50%", transform: "translate(-50%,-50%)",
    boxShadow: "0 0 24px 4px rgba(59,130,246,0.4)"
  }}
  initial={{ scale: 0, opacity: 0 }}
  animate={{ scale: [0, 1.4, 1], opacity: 1 }}
  transition={{ duration: 0.8, delay: 0.6 }} />
```

## Rotating Word Flipper (Hero)

```tsx
const WORDS = ["Scaffolding", "Architecture", "Development", "Tooling"];
const [index, setIndex] = useState(0);
useEffect(() => {
  const t = setInterval(() => setIndex(i => (i + 1) % WORDS.length), 2200);
  return () => clearInterval(t);
}, []);

<span className="overflow-hidden inline-block align-bottom">
  <AnimatePresence mode="wait">
    <motion.span key={WORDS[index]}
      className="inline-block text-accent"
      initial={{ y: "110%", opacity: 0 }}
      animate={{ y: "0%", opacity: 1 }}
      exit={{ y: "-110%", opacity: 0 }}
      transition={{ duration: 0.38, ease: [0.32, 0, 0.67, 0] }}>
      {WORDS[index]}
    </motion.span>
  </AnimatePresence>
</span>
```

## Timeline Connector Line (HowItWorks)

```tsx
// Growing vertical line driven by scroll
<motion.div
  className="absolute left-[19px] w-px bg-accent/40"
  style={{ top: "20px" }}
  initial={{ height: 0 }}
  whileInView={{ height: "calc(100% - 20px)" }}
  viewport={{ once: true, margin: "-100px" }}
  transition={{ duration: 1.5, ease: "easeOut" }} />
```

## Tab Indicator (Shared Layout Animation)

```tsx
{tabs.map(tab => (
  <button key={tab.id} onClick={() => setActive(tab.id)} className="relative px-4 py-2">
    {tab.label}
    {active === tab.id && (
      <motion.div
        layoutId="tab-indicator"
        className="absolute bottom-0 left-0 right-0 h-px bg-accent"
        transition={{ type: "spring", stiffness: 500, damping: 40 }} />
    )}
  </button>
))}
```

## Tab Content Transition

```tsx
<AnimatePresence mode="wait">
  <motion.div key={activeTab}
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -8 }}
    transition={{ duration: 0.2 }}>
    {/* tab content */}
  </motion.div>
</AnimatePresence>
```

## Mobile Menu (Height Animation)

```tsx
<AnimatePresence>
  {menuOpen && (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
      className="overflow-hidden bg-background/95 backdrop-blur-lg border-b border-border">
      {/* nav links */}
    </motion.div>
  )}
</AnimatePresence>
```

## Marquee (TechStack)

Two parallel tracks, one slightly faster, both looping:
```tsx
// Track 1 — 28s
animate={{ x: ["0%", "-50%"] }}
transition={{ duration: 28, ease: "linear", repeat: Infinity }}

// Track 2 — 32s (different speed for visual interest)
animate={{ x: ["0%", "-50%"] }}
transition={{ duration: 32, ease: "linear", repeat: Infinity }}
```

The content array is always duplicated (`[...items, ...items]`) so the loop is seamless.

## Glow Effect (CSS Shadow Utility)

```tsx
// Blue glow on accent elements
style={{ boxShadow: "0 0 24px 4px rgba(59,130,246,0.4)" }}

// Soft glow on cards (hover state, via Tailwind arbitrary)
className="hover:shadow-[0_0_20px_2px_rgba(59,130,246,0.15)]"
```

## Card Hover Border

```tsx
// Inset border appears on hover
className="transition-shadow duration-200"
style={{ boxShadow: "none" }}
// on hover:
style={{ boxShadow: "inset 0 0 0 1px #3b82f6" }}
// Or with group-hover in Tailwind:
className="group-hover:[box-shadow:inset_0_0_0_1px_#3b82f6]"
```
