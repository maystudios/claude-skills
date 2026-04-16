# Content & Copywriting Template

Use this as a scaffold for filling in product-specific content.
Replace all `[PLACEHOLDER]` values with actual product content.

## Product Information Gathering

Before building, collect from the user:
1. **Product name** — short, memorable
2. **One-liner** — what it does in 10 words or less
3. **Target audience** — developers? specific stack? company size?
4. **Core value props** — top 3-6 features/benefits
5. **Install command** — the actual `npx` / `npm install -g` / `pip install` command
6. **GitHub URL** — for the header and footer links
7. **Tech stack** — what it's built with / what it integrates with
8. **4-step workflow** — Install → Create/Configure → Develop → Ship
9. **Accent color** — blue (default), green (SaaS), purple (AI), orange (creative)

---

## Navbar

```
Brand:     [ProductName]
Links:     Features | How it works | Stack | Docs
CTA:       Get Started  |  GitHub
```

---

## Hero

**Eyebrow label:**
```
[Category]: CLI Tool | Developer Library | SaaS | AI Tool | Framework
```

**Headline pattern (animated word rotation):**
```
AI-Powered [Word1]
             [Word2]
             [Word3]
             [Word4]

Options:
- Scaffolding / Architecture / Development / Tooling
- Setup / Configuration / Deployment / Monitoring
- Generation / Testing / Documentation / Integration
```

**Subheadline (2-3 sentences):**
```
[ProductName] is a [CLI tool / library / framework] that [does X] for [target].
It [key differentiator] so you can [outcome].
[Social proof or scale: "Used by 1000+ developers" or "Production-ready in minutes."]
```

**CTAs:**
```
Primary:   Get Started  (links to #docs)
Secondary: View on GitHub  (links to GitHub)
```

**Terminal command:**
```bash
# Choose one pattern:
npx [product-name] create my-project
npm install -g [product-name]
pip install [product-name]
brew install [product-name]
curl -fsSL https://example.com/install.sh | sh
```

---

## Features Section

**Header:**
```
Eyebrow:  What's included
Heading:  Everything you need to [outcome]
Body:     [1-2 sentences on what these features collectively enable]
```

**Feature cards (6 items, 3-col grid):**
Each needs: icon (Lucide), title (2-3 words), description (1-2 sentences)

```
Pattern — use these categories:
1. Speed/Setup     — "One command", "Zero config", "Instant scaffold"
2. Architecture    — "Clean structure", "Best practices", "Patterns included"
3. DX/Tooling      — "Type safe", "Hot reload", "Rich CLI output"
4. Modularity      — "Pick your features", "Opt-in modules", "Composable"
5. AI Integration  — "AI-assisted", "Agent-ready", "LLM context"
6. Production      — "CI/CD ready", "Testing built-in", "Deploy anywhere"
```

---

## How It Works

**Header:**
```
Eyebrow:  Getting started
Heading:  Up and running in [X] minutes
```

**4 steps:**
```
Step 01: Install
  desc: [Install command description]
  cmd:  npm install -g [product-name]

Step 02: Create / Init
  desc: [Scaffold description with module selection]
  cmd:  [product-name] create my-project

Step 03: Develop
  desc: [Dev workflow description]
  cmd:  cd my-project && npm run dev

Step 04: Ship
  desc: [Build/deploy description]
  cmd:  npm run build (or deploy command)
```

---

## Tech Stack Marquee

Two tracks of 6-10 items each. Mix:
- **Core dependencies** (React, TypeScript, Node.js, etc.)
- **Integrations** (GitHub, Docker, Vercel, etc.)
- **Dev tools** (ESLint, Jest, Playwright, etc.)
- **Standards** (REST API, OpenAPI, GraphQL, etc.)

```
Track 1 (slower, 28s): Core framework + runtime deps
Track 2 (faster, 34s): Dev tools + integrations
```

---

## Docs / Reference Section

**5 standard tabs:**

| Tab            | Content                                              |
|---------------|------------------------------------------------------|
| Getting Started | Install, init, first run — 3-5 code blocks         |
| Commands       | Full CLI command reference with flags                |
| Configuration  | Config file schema with all options                  |
| Examples       | Real-world usage scenarios with code                 |
| FAQ / Advanced | Common questions, edge cases, migration guide        |

**Code block conventions:**
```tsx
// Always show language label
// Always include a copy button
// Use syntax-like coloring with text-accent for keywords
// Wrap in bg-surface border border-border rounded-sm
```

---

## Footer

```
Left:  [product-name]  |  v[version]  |  MIT License
Right: GitHub link  |  npm link  |  Back to top
```

---

## Color Accent Guide by Product Type

| Product Type          | Accent Color  | CSS value   |
|-----------------------|---------------|-------------|
| CLI / Dev Tool        | Blue (default) | `#3b82f6`  |
| SaaS / B2B            | Indigo/Purple  | `#6366f1`  |
| AI / ML               | Violet         | `#8b5cf6`  |
| Security / DevSecOps  | Emerald green  | `#10b981`  |
| Data / Analytics      | Cyan           | `#06b6d4`  |
| Design / Creative     | Orange/Amber   | `#f59e0b`  |
| Open Source / Infra   | Blue (default) | `#3b82f6`  |

---

## Rotating Words by Domain

**CLI tools:** Scaffolding / Architecture / Development / Tooling
**Web frameworks:** Pages / Components / Layouts / Themes
**AI tools:** Generation / Reasoning / Agents / Automation
**Data tools:** Pipelines / Transforms / Queries / Reports
**DevOps:** Deployments / Monitoring / Scaling / Pipelines
**APIs:** Endpoints / Authentication / Validation / Documentation
