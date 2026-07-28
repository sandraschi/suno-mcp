import { AlertTriangle, FileJson, ScanSearch } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchReconOutputDir,
  getApiBase,
  triggerReconCaptureCurrent,
  triggerReconFindElements,
} from "@/lib/backend";

export function Recon() {
  const [outDir, setOutDir] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"capture" | "elements" | null>(null);

  const loadDir = useCallback(async () => {
    try {
      const { path } = await fetchReconOutputDir();
      setOutDir(path);
    } catch {
      setOutDir(null);
    }
  }, []);

  useEffect(() => {
    void loadDir();
  }, [loadDir]);

  const runCapture = async () => {
    setBusy("capture");
    setError(null);
    setLastMessage(null);
    try {
      const res = await triggerReconCaptureCurrent();
      setLastMessage(res.message);
      void loadDir();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const runElements = async () => {
    setBusy("elements");
    setError(null);
    setLastMessage(null);
    try {
      const res = await triggerReconFindElements();
      setLastMessage(res.message);
      void loadDir();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Playwright recon
        </h2>
        <p className="mt-1 text-slate-400">
          Runs on the <strong className="text-slate-200">same Chromium</strong>{" "}
          session as MCP tools (
          <code className="text-slate-300">get_shared_browser_manager</code>).
          Open Suno via{" "}
          <code className="text-slate-300">suno_open_browser</code> or{" "}
          <code className="text-slate-300">recon_start_session</code>, navigate,
          then analyze here.
        </p>
      </div>

      <div className="flex flex-wrap gap-2 rounded-md border border-amber-900/60 bg-amber-950/30 px-4 py-3 text-sm text-amber-100">
        <AlertTriangle className="h-5 w-5 shrink-0 text-amber-400" />
        <span>
          This does <strong>not</strong> see your normal Chrome/Edge window—only
          the Playwright browser started by this server. Backend:{" "}
          <code className="text-amber-50">{getApiBase()}</code>
        </span>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button
          className="bg-emerald-700 hover:bg-emerald-600"
          disabled={busy !== null}
          onClick={() => void runCapture()}
        >
          <ScanSearch className="mr-2 h-4 w-4" />
          {busy === "capture" ? "Capturing…" : "Capture DOM (current page)"}
        </Button>
        <Button
          variant="secondary"
          disabled={busy !== null}
          onClick={() => void runElements()}
        >
          <FileJson className="mr-2 h-4 w-4" />
          {busy === "elements" ? "Mapping…" : "Map interactive elements"}
        </Button>
      </div>

      {outDir && (
        <p className="text-xs text-slate-500">
          Output directory: <code className="text-slate-400">{outDir}</code>
        </p>
      )}

      {error && (
        <Card className="border-red-900/60 bg-red-950/30">
          <CardHeader>
            <CardTitle className="text-red-200">Request failed</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap font-mono text-sm text-red-100">
              {error}
            </pre>
          </CardContent>
        </Card>
      )}

      {lastMessage && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">
              Result (also in MCP / disk)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="max-h-[480px] overflow-auto whitespace-pre-wrap font-mono text-sm text-slate-300">
              {lastMessage}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
