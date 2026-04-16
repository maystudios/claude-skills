import { motion } from "motion/react";

// ADAPT: replace with 4 steps — typically: install → create → develop → ship
const steps = [
  {
    number: "01",
    title: "Install",
    description: "Install the CLI globally via npm. One command to get the full toolchain.",
    code: "npm install -g maxsim-flutter",
  },
  {
    number: "02",
    title: "Create",
    description: "Scaffold your app with only the modules you need. Clean Architecture included by default.",
    code: "maxsim-flutter create my_app --modules auth,api,theme",
  },
  {
    number: "03",
    title: "Develop",
    description: "AI agents collaborate to implement features from your PRD — architect, builder, tester, reviewer.",
    code: "maxsim-flutter plan --prd ./PRD.md",
  },
  {
    number: "04",
    title: "Ship",
    description: "Built-in CI/CD pipeline deploys your app. Quality gates enforce code standards on every build.",
    code: "maxsim-flutter deploy --env production",
  },
];

const stepVariants = {
  hidden: { opacity: 0, x: -24 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { duration: 0.5, delay: i * 0.12, ease: "easeOut" as const },
  }),
};

export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-background py-24 px-6 border-t border-border">
      <div className="max-w-4xl mx-auto">
        {/* Heading */}
        <div className="mb-16">
          {/* ADAPT: eyebrow label */}
          <p className="text-xs uppercase tracking-widest text-muted font-medium mb-4">
            Getting started
          </p>
          <h2 className="text-4xl md:text-5xl font-bold text-foreground leading-tight">
            How It Works
          </h2>
          {/* ADAPT: subtitle */}
          <p className="mt-4 text-muted text-lg max-w-xl">
            From install to production in four steps. No ceremony, no boilerplate.
          </p>
        </div>

        {/* Steps */}
        <div className="relative">
          {/* Connecting line */}
          <motion.div
            className="absolute left-[19px] top-10 bottom-10 w-px bg-border"
            initial={{ scaleY: 0, originY: 0 }}
            whileInView={{ scaleY: 1 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />

          <div className="flex flex-col gap-0">
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                custom={i}
                variants={stepVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-60px" }}
                className="relative flex gap-8 pb-12 last:pb-0"
              >
                {/* Number circle */}
                <div className="relative z-10 shrink-0 flex items-start pt-1">
                  <div className="w-10 h-10 rounded-full border border-border bg-background flex items-center justify-center group-hover:border-accent transition-colors">
                    <span className="text-xs font-mono text-accent font-bold">
                      {step.number}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 pt-1">
                  <h3 className="text-foreground font-bold text-xl tracking-tight mb-2">
                    {step.title}
                  </h3>
                  <p className="text-muted text-sm leading-relaxed mb-4 max-w-lg">
                    {step.description}
                  </p>
                  {/* Code snippet */}
                  <div className="inline-flex items-center gap-3 bg-surface border border-border px-4 py-2.5 rounded-sm">
                    <span className="text-accent font-mono text-xs select-none">$</span>
                    <code className="font-mono text-xs text-foreground/90 whitespace-nowrap">
                      {step.code}
                    </code>
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
