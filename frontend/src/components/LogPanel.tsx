import { TerminalSquare } from "lucide-react";

import type { RunLog } from "../types/evaluation";

export function LogPanel({ logs }: { logs: RunLog[] }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-100">
        <TerminalSquare className="h-4 w-4 text-cyan-200" />
        运行日志
      </div>
      <div className="mt-3 max-h-56 space-y-2 overflow-auto pr-1">
        {logs.length > 0 ? (
          logs.map((log, index) => (
            <div key={`${log.time}-${index}`} className="grid grid-cols-[78px_1fr] gap-2 text-xs">
              <span className={log.level === "error" ? "text-red-200" : "text-cyan-200"}>{log.level}</span>
              <span className="text-slate-400">{log.message}</span>
            </div>
          ))
        ) : (
          <p className="text-sm text-slate-500">运行事件将在评估过程中写入。</p>
        )}
      </div>
    </div>
  );
}
