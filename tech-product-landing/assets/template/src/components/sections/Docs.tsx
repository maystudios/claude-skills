import { useState, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Copy, Check, Terminal, Layers, Settings, Bot, Package } from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

// ADAPT: rename tab IDs and add/remove tabs to match your docs structure
type TabId = "getting-started" | "commands" | "modules" | "configuration" | "agent-teams";

// ─── Copy Button ──────────────────────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <button
      onClick={handleCopy}
      className="absolute top-3 right-3 p-1.5 rounded text-muted hover:text-foreground hover:bg-surface-light transition-colors"
      aria-label="Copy code"
    >
      <AnimatePresence mode="wait" initial={false}>
        {copied ? (
          <motion.span
            key="check"
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.7 }}
            transition={{ duration: 0.15 }}
          >
            <Check size={14} className="text-accent" />
          </motion.span>
        ) : (
          <motion.span
            key="copy"
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.7 }}
            transition={{ duration: 0.15 }}
          >
            <Copy size={14} />
          </motion.span>
        )}
      </AnimatePresence>
    </button>
  );
}

// ─── Code Block ───────────────────────────────────────────────────────────────

function CodeBlock({ code, language = "bash" }: { code: string; language?: string }) {
  return (
    <div className="relative group">
      <div className="flex items-center justify-between bg-surface-light px-4 py-2 rounded-t border border-border border-b-0">
        <span className="text-xs text-muted font-mono uppercase tracking-wider">{language}</span>
        <CopyButton text={code.trim()} />
      </div>
      <pre className="bg-surface rounded-b border border-border overflow-x-auto p-4 text-sm font-mono leading-relaxed">
        <code className="text-zinc-300 whitespace-pre">{code.trim()}</code>
      </pre>
    </div>
  );
}

// ─── Section heading ──────────────────────────────────────────────────────────

function DocHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-foreground font-bold text-xl tracking-tight mb-4">{children}</h3>
  );
}

function DocSubheading({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="text-foreground font-semibold text-base tracking-tight mb-3 mt-6">{children}</h4>
  );
}

function DocText({ children }: { children: React.ReactNode }) {
  return <p className="text-muted text-sm leading-relaxed mb-4">{children}</p>;
}

// ─── Tab: Getting Started ─────────────────────────────────────────────────────
// ADAPT: replace with your actual installation instructions

function GettingStarted() {
  return (
    <div className="space-y-8">
      <div>
        <DocHeading>Installation</DocHeading>
        <DocText>
          Requirements: Node.js &gt;= 18, Flutter SDK (optional at scaffold time)
        </DocText>
      </div>

      <div>
        <DocSubheading>Quick Install</DocSubheading>
        <CodeBlock
          language="bash"
          code={`npm install -g maxsim-flutter`}
        />
      </div>

      <div>
        <DocSubheading>Or use npx (no install needed)</DocSubheading>
        <CodeBlock
          language="bash"
          code={`npx maxsim-flutter create my_app`}
        />
      </div>

      <div>
        <DocSubheading>Interactive Mode</DocSubheading>
        <DocText>
          Launch the interactive wizard — prompts for app name, org ID, modules, and platforms.
        </DocText>
        <CodeBlock
          language="bash"
          code={`maxsim-flutter create
# Prompts for: app name, org ID, modules, platforms`}
        />
      </div>

      <div>
        <DocSubheading>Non-Interactive Mode</DocSubheading>
        <DocText>
          Pass all options as flags for CI/CD or scripted setups.
        </DocText>
        <CodeBlock
          language="bash"
          code={`maxsim-flutter create shop_app \\
  --org com.acme \\
  --modules auth,api,database,theme \\
  --platforms android,ios,web \\
  --yes`}
        />
      </div>
    </div>
  );
}

// ─── Tab: Commands ────────────────────────────────────────────────────────────
// ADAPT: replace with your CLI's actual commands

interface CommandDef {
  name: string;
  signature: string;
  description: string;
  flags?: string[];
  example: string;
}

const commands: CommandDef[] = [
  {
    name: "create",
    signature: "create [app-name]",
    description: "Scaffold a new Flutter project with selected modules and platforms.",
    flags: ["--org", "--modules", "--platforms", "--auth-provider", "--config", "--yes", "--dry-run", "--no-claude"],
    example: `maxsim-flutter create shop_app \\
  --org com.acme \\
  --modules auth,api,database,theme \\
  --platforms android,ios,web \\
  --yes`,
  },
  {
    name: "add",
    signature: "add [module]",
    description: "Add a module to an existing Flutter project.",
    example: `maxsim-flutter add push --project-dir ~/my_app`,
  },
  {
    name: "plan",
    signature: "plan [app-name]",
    description: "Bootstrap an AI-guided planning workspace with PRD, user stories, and agent prompts.",
    example: `maxsim-flutter plan my_app --description "A chat app for small teams"`,
  },
  {
    name: "migrate",
    signature: "migrate [path]",
    description: "Analyze and migrate existing Flutter projects to Clean Architecture.",
    example: `maxsim-flutter migrate --analysis-only`,
  },
];

function Commands() {
  return (
    <div className="space-y-10">
      {commands.map((cmd) => (
        <div key={cmd.name} className="border-l-2 border-accent pl-6">
          <div className="flex flex-wrap items-center gap-3 mb-2">
            <code className="text-accent font-mono font-semibold text-base">{cmd.signature}</code>
          </div>
          <DocText>{cmd.description}</DocText>

          {cmd.flags && (
            <div className="mb-4">
              <p className="text-xs uppercase tracking-widest text-muted font-medium mb-2">Flags</p>
              <div className="flex flex-wrap gap-2">
                {cmd.flags.map((f) => (
                  <span
                    key={f}
                    className="font-mono text-xs px-2 py-0.5 rounded bg-surface border border-border text-zinc-400"
                  >
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}

          <CodeBlock language="bash" code={cmd.example} />
        </div>
      ))}
    </div>
  );
}

// ─── Tab: Modules ─────────────────────────────────────────────────────────────
// ADAPT: replace with your product's modules/options/plugins

const modules = [
  { name: "core", description: "Clean Architecture + Riverpod + go_router + freezed", options: "Always included" },
  { name: "auth", description: "Login, register, session management", options: "firebase, supabase, custom" },
  { name: "api", description: "Dio HTTP client with interceptors", options: "Base URL, timeout" },
  { name: "theme", description: "Material 3 theming with seed colors", options: "Seed color, dark mode" },
  { name: "database", description: "Local persistence", options: "drift, hive, isar" },
  { name: "i18n", description: "ARB-based multi-language support", options: "Default locale, supported locales" },
  { name: "push", description: "Push notifications", options: "firebase, onesignal" },
  { name: "analytics", description: "Firebase Analytics + route observer", options: "—" },
  { name: "cicd", description: "CI/CD pipeline configuration", options: "github, gitlab, bitbucket" },
  { name: "deep-linking", description: "App Links + go_router integration", options: "Scheme, host" },
];

function Modules() {
  return (
    <div className="space-y-6">
      <DocText>
        Modules are opt-in features you select at scaffold time or add later with{" "}
        <code className="font-mono text-accent text-xs bg-surface px-1.5 py-0.5 rounded border border-border">
          maxsim-flutter add
        </code>
        . The <code className="font-mono text-accent text-xs bg-surface px-1.5 py-0.5 rounded border border-border">core</code> module is always included.
      </DocText>

      {/* Desktop table */}
      <div className="hidden md:block overflow-hidden border border-border rounded">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface border-b border-border">
              <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-muted font-medium w-32">Module</th>
              <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-muted font-medium">Description</th>
              <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-muted font-medium w-52">Options</th>
            </tr>
          </thead>
          <tbody>
            {modules.map((mod, i) => (
              <motion.tr
                key={mod.name}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04, duration: 0.3 }}
                className="border-b border-border last:border-0 hover:bg-surface transition-colors"
              >
                <td className="px-4 py-3">
                  <code className="font-mono text-accent text-xs">{mod.name}</code>
                </td>
                <td className="px-4 py-3 text-muted">{mod.description}</td>
                <td className="px-4 py-3 text-zinc-500 text-xs font-mono">{mod.options}</td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden space-y-3">
        {modules.map((mod, i) => (
          <motion.div
            key={mod.name}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04, duration: 0.3 }}
            className="border border-border rounded p-4 bg-surface"
          >
            <code className="font-mono text-accent text-sm font-semibold">{mod.name}</code>
            <p className="text-muted text-sm mt-1">{mod.description}</p>
            {mod.options !== "—" && (
              <p className="text-zinc-500 text-xs font-mono mt-1.5">{mod.options}</p>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// ─── Tab: Configuration ───────────────────────────────────────────────────────
// ADAPT: replace with your product's config file format

const configYaml = `version: "1"
project:
  name: my_app
  orgId: com.example
  description: "My Flutter app"
modules:
  auth:
    enabled: true
    provider: firebase
  api:
    enabled: true
    baseUrl: https://api.example.com
    timeout: 30000
  database:
    enabled: true
    engine: drift
  theme:
    enabled: true
    seedColor: "#6750A4"
    useMaterial3: true
    darkMode: true
  i18n:
    enabled: true
    defaultLocale: en
    supportedLocales: [en, es]
platforms:
  - android
  - ios
  - web
claude:
  enabled: true
  generateAgents: true
  agentTeams: true`;

function Configuration() {
  return (
    <div className="space-y-6">
      <div>
        <DocHeading>maxsim.config.yaml</DocHeading>
        <DocText>
          Place <code className="font-mono text-accent text-xs bg-surface px-1.5 py-0.5 rounded border border-border">maxsim.config.yaml</code> in your project root
          to define default settings. All values can be overridden by CLI flags.
        </DocText>
      </div>
      <CodeBlock language="yaml" code={configYaml} />
    </div>
  );
}

// ─── Tab: Agent Teams ─────────────────────────────────────────────────────────
// ADAPT: replace with your fifth documentation topic

const agentSteps = [
  {
    number: "01",
    title: "Scaffold with Claude enabled",
    description: "Create your project with the default settings — Claude Code integration is on by default.",
    code: `maxsim-flutter create task_manager --modules auth,api --yes`,
  },
  {
    number: "02",
    title: "Generated .claude/ directory",
    description: "The scaffold generates agent definition files for each role in the development team.",
    code: `.claude/
├── agents/
│   ├── architect.md
│   ├── builder.md
│   ├── tester.md
│   ├── reviewer.md
│   └── docs.md
└── prd.json`,
  },
  {
    number: "03",
    title: "Open Claude Code and start the team",
    description: 'In Claude Code, instruct it to bootstrap your agent team from the PRD.',
    code: `# In Claude Code terminal:
"Create an agent team from prd.json"`,
  },
  {
    number: "04",
    title: "Autonomous agent pipeline",
    description: "Agents work in sequence with handoffs between each role.",
    code: `Architect → plans architecture & interfaces
Builders  → implement feature by feature
Tester    → writes & runs test suites
Reviewer  → enforces standards & quality
Docs      → generates documentation`,
  },
  {
    number: "05",
    title: "Quality gates enforced",
    description: "Every phase must pass all three quality gates before proceeding.",
    code: `flutter analyze   # 0 issues required
flutter test      # all tests must pass
dart format       # consistent formatting`,
  },
  {
    number: "06",
    title: "PRD-driven development",
    description: "User stories from prd.json are executed phase by phase, with progress tracked automatically.",
    code: `# Phase completion example
✓ Phase 1: Auth module — 12/12 stories done
✓ Phase 2: API layer  —  8/8 stories done
→ Phase 3: Dashboard  —  0/6 stories (next)`,
  },
];

function AgentTeams() {
  return (
    <div className="space-y-8">
      <div>
        <DocHeading>Claude Code Agent Teams</DocHeading>
        <DocText>
          Maxsim scaffolds a complete multi-agent development team alongside your Flutter project.
          Each agent has a defined role, tool access, and quality bar — enabling autonomous
          PRD-driven feature development.
        </DocText>
      </div>

      <div className="space-y-6">
        {agentSteps.map((step, i) => (
          <motion.div
            key={step.number}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07, duration: 0.35 }}
            className="grid grid-cols-1 md:grid-cols-[80px_1fr] gap-4"
          >
            <div className="flex md:flex-col items-center md:items-start gap-3 md:gap-0">
              <span className="text-2xl font-bold text-accent font-mono leading-none">{step.number}</span>
              <div className="flex-1 md:flex-none md:mt-4 md:w-px md:self-stretch md:bg-border" />
            </div>
            <div className="space-y-3 pb-2">
              <h4 className="text-foreground font-semibold text-sm tracking-tight">{step.title}</h4>
              <p className="text-muted text-sm leading-relaxed">{step.description}</p>
              <CodeBlock language="bash" code={step.code} />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// ─── Tab definitions ──────────────────────────────────────────────────────────
// ADAPT: rename tabs and icons to match your documentation structure

const tabs: { id: TabId; label: string; Icon: React.ElementType }[] = [
  { id: "getting-started", label: "Getting Started", Icon: Terminal },
  { id: "commands", label: "Commands", Icon: Terminal },
  { id: "modules", label: "Modules", Icon: Package },
  { id: "configuration", label: "Configuration", Icon: Settings },
  { id: "agent-teams", label: "Agent Teams", Icon: Bot },
];

function tabContent(id: TabId) {
  switch (id) {
    case "getting-started": return <GettingStarted />;
    case "commands": return <Commands />;
    case "modules": return <Modules />;
    case "configuration": return <Configuration />;
    case "agent-teams": return <AgentTeams />;
  }
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function Docs() {
  const [activeTab, setActiveTab] = useState<TabId>("getting-started");
  const tabRefs = useRef<Map<TabId, HTMLButtonElement>>(new Map());

  return (
    <section id="docs" className="bg-background py-24 px-6">
      <div className="max-w-6xl mx-auto">

        {/* Section header */}
        <motion.div
          className="mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
        >
          {/* ADAPT: eyebrow and subtitle */}
          <p className="text-xs uppercase tracking-widest text-muted font-medium mb-4">
            Reference
          </p>
          <h2 className="text-4xl md:text-5xl font-bold text-foreground leading-tight">
            Documentation
          </h2>
          <p className="mt-4 text-muted text-lg max-w-xl">
            Everything you need to know — from installation to AI agent teams.
          </p>
        </motion.div>

        {/* Tab bar */}
        <div className="relative mb-0 overflow-x-auto">
          <div className="flex min-w-max border-b border-border">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  ref={(el) => { if (el) tabRefs.current.set(tab.id, el); }}
                  onClick={() => setActiveTab(tab.id)}
                  className={[
                    "relative px-5 py-3 text-sm font-medium transition-colors whitespace-nowrap",
                    isActive ? "text-foreground" : "text-muted hover:text-foreground",
                  ].join(" ")}
                >
                  <span className="flex items-center gap-2">
                    {tab.label}
                  </span>
                  {isActive && (
                    <motion.div
                      layoutId="tab-indicator"
                      className="absolute bottom-0 left-0 right-0 h-px bg-accent"
                      transition={{ type: "spring", stiffness: 500, damping: 40 }}
                    />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab content */}
        <div className="border border-t-0 border-border rounded-b bg-surface">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="p-6 md:p-10"
            >
              {tabContent(activeTab)}
            </motion.div>
          </AnimatePresence>
        </div>

      </div>
    </section>
  );
}
