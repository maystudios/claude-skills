import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// ADAPT: fetch version from npm, or replace with a static string
async function fetchNpmVersion(pkg: string): Promise<string> {
  try {
    const res = await fetch(`https://registry.npmjs.org/${pkg}/latest`);
    const data = (await res.json()) as { version?: string };
    return data.version ?? "0.0.0";
  } catch {
    return "0.0.0";
  }
}

export default defineConfig(async () => {
  // ADAPT: replace "maxsim-flutter" with your npm package name
  // Or use a static version: const version = "1.0.0";
  const version = await fetchNpmVersion("maxsim-flutter");

  return {
    base: "/",
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    define: {
      // ADAPT: rename __MAXSIM_VERSION__ to match your product
      // Update all usages in Hero.tsx and Footer.tsx accordingly
      __MAXSIM_VERSION__: JSON.stringify(version),
    },
  };
});
