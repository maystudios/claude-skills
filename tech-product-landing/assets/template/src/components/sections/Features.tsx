import { motion } from "motion/react";
import { Layers, Blocks, Bot, Terminal, GitBranch, ShieldCheck } from "lucide-react";

// ADAPT: replace with 6 features relevant to your product
// Choose icons from lucide-react — keep exactly 6 (fills 3-col grid)
const features = [
  {
    icon: Layers,
    title: "Clean Architecture",
    description:
      "Production-ready project structure with domain, data, and presentation layers following SOLID principles.",
  },
  {
    icon: Blocks,
    title: "9 Modular Features",
    description:
      "Auth, API, Database, Theme, i18n, Push Notifications, Analytics, CI/CD, and Deep Linking — pick what you need.",
  },
  {
    icon: Bot,
    title: "Claude Code Integration",
    description:
      "Built-in AI agent teams with architect, builder, tester, and reviewer for autonomous development.",
  },
  {
    icon: Terminal,
    title: "One Command Setup",
    description:
      "From zero to full Flutter project with a single CLI command. Interactive or fully automated.",
  },
  {
    icon: GitBranch,
    title: "Plan & Migrate",
    description:
      "Bootstrap AI-guided planning workspaces or migrate existing Flutter projects to Clean Architecture.",
  },
  {
    icon: ShieldCheck,
    title: "Quality Gates",
    description:
      "Automated flutter analyze, flutter test, and dart format enforcement on every generated project.",
  },
];

const containerVariants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

export function Features() {
  return (
    <section id="features" className="bg-background py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-16">
          {/* ADAPT: section eyebrow label */}
          <p className="text-xs uppercase tracking-widest text-muted font-medium mb-4">
            What's included
          </p>
          <h2 className="text-4xl md:text-5xl font-bold text-foreground leading-tight">
            Features
          </h2>
          {/* ADAPT: section subtitle */}
          <p className="mt-4 text-muted text-lg max-w-xl">
            Everything you need to ship production-quality Flutter apps — without the boilerplate.
          </p>
        </div>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-border"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-80px" }}
        >
          {features.map(({ icon: Icon, title, description }) => (
            <motion.div
              key={title}
              variants={cardVariants}
              whileHover="hover"
              className="relative bg-background p-8 group"
            >
              {/* Blue inset border on hover */}
              <motion.div
                className="absolute inset-0 pointer-events-none"
                initial={{ opacity: 0 }}
                whileHover={{ opacity: 1 }}
                transition={{ duration: 0.2 }}
                style={{
                  boxShadow: "inset 0 0 0 1px #3b82f6",
                }}
              />

              <div className="mb-5 inline-flex items-center justify-center w-10 h-10 rounded-none bg-surface text-accent">
                <Icon size={20} strokeWidth={1.5} />
              </div>

              <h3 className="text-foreground font-bold text-lg mb-2 tracking-tight">
                {title}
              </h3>
              <p className="text-muted text-sm leading-relaxed">{description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
