// graphify OpenCode plugin
// Injects a knowledge graph reminder before bash tool calls when the graph exists.
//
// IMPORTANT: keep the reminder string free of backticks and $(...) constructs.
// The hook prepends `echo "<reminder>" && <cmd>` to the user's bash command;
// backticks inside the double-quoted echo trigger bash command substitution,
// which both corrupts tool output and silently executes the very graphify
// command we are only suggesting. Plain words render fine in opencode's TUI.
import { existsSync, statSync } from "fs";
import { join } from "path";

// Remind on the first bash call, then at most once every REMIND_EVERY bash
// calls — a single one-shot reminder was wasted when the first call was
// something trivial like pwd or ls.
const REMIND_EVERY = 10;

// Graphs older than this get a "run graphify update ." nudge appended to the
// reminder, so a stale graph is never silently recommended.
const STALE_AFTER_DAYS = 3;

const graphAgeDays = (directory) => {
  try {
    const mtimeMs = statSync(join(directory, "graphify-out", "graph.json")).mtimeMs;
    return (Date.now() - mtimeMs) / (24 * 60 * 60 * 1000);
  } catch {
    return null;
  }
};

export const GraphifyPlugin = async ({ directory }) => {
  let bashCalls = 0;

  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return;
      if (!existsSync(join(directory, "graphify-out", "graph.json"))) return;

      bashCalls += 1;
      if (bashCalls !== 1 && bashCalls % REMIND_EVERY !== 0) return;

      const ageDays = graphAgeDays(directory);
      const staleHint =
        ageDays !== null && ageDays > STALE_AFTER_DAYS
          ? ` Graph is ~${Math.floor(ageDays)} days old; run graphify update . to refresh it (AST-only, no API cost).`
          : "";

      // ';' not '&&' — Windows PowerShell 5.1 rejects '&&' as a statement
      // separator, breaking the first bash command of the session (#1646).
      output.args.command =
        'echo "[graphify] knowledge graph at graphify-out/. For focused questions, run graphify query with your question (scoped subgraph, usually much smaller than GRAPH_REPORT.md) instead of grepping raw files. Use graphify path for relationships between two nodes and graphify explain for a single concept. Read GRAPH_REPORT.md only for broad architecture context.' +
        staleHint +
        '" ; ' +
        output.args.command;
    },
  };
};
