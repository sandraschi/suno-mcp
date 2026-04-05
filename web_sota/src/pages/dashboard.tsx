import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Globe, Shield, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    fetchBrowserStatus,
    fetchHealth,
    formatUptime,
    getApiBase,
    type HealthPayload,
    type StatusPayload,
} from "@/lib/backend";

export function Dashboard() {
    const [health, setHealth] = useState<HealthPayload | null>(null);
    const [browser, setBrowser] = useState<StatusPayload | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [updated, setUpdated] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [h, s] = await Promise.all([fetchHealth(), fetchBrowserStatus()]);
            setHealth(h);
            setBrowser(s);
            setUpdated(new Date().toLocaleString());
        } catch (e) {
            setHealth(null);
            setBrowser(null);
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void load();
        const id = setInterval(() => void load(), 5000);
        return () => clearInterval(id);
    }, [load]);

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Suno MCP Dashboard</h2>
                    <p className="text-slate-400">
                        Data from FastAPI at <code className="text-slate-300">{getApiBase()}</code> — not fabricated.
                    </p>
                </div>
                <Button variant="outline" size="sm" onClick={() => void load()} disabled={loading}>
                    {loading ? "Refreshing…" : "Refresh"}
                </Button>
            </div>

            {error && (
                <div className="rounded-md border border-amber-900/80 bg-amber-950/40 px-4 py-3 text-sm text-amber-100">
                    <strong className="text-amber-50">Backend unreachable.</strong> {error} — Start the API:{" "}
                    <code className="rounded bg-slate-900 px-1">web_sota\start.ps1</code> (or uvicorn on the port in{" "}
                    <code className="rounded bg-slate-900 px-1">VITE_API_BASE_URL</code>).
                </div>
            )}

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">API health</CardTitle>
                        <Shield className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {health?.status ?? (loading ? "…" : "—")}
                        </div>
                        <p className="text-xs text-slate-400">GET /health</p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Process uptime</CardTitle>
                        <Activity className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {health != null ? formatUptime(health.uptime) : loading ? "…" : "—"}
                        </div>
                        <p className="text-xs text-slate-400">Server uptime (not Suno SLA)</p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Tools (MCP)</CardTitle>
                        <Wrench className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {health?.tools_loaded ?? (loading ? "…" : "—")}
                        </div>
                        <p className="text-xs text-slate-400">Registered tools (help text)</p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Playwright page</CardTitle>
                        <Globe className="h-4 w-4 text-orange-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {browser == null
                                ? loading
                                    ? "…"
                                    : "—"
                                : browser.page_ready
                                  ? "Ready"
                                  : "No / idle"}
                        </div>
                        <p className="text-xs text-slate-400">
                            {browser?.browser_open ? "Browser process up" : "No active browser context"}
                        </p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Playwright URL</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="break-all font-mono text-sm text-slate-300">
                            {browser?.current_url ?? "—"}
                        </p>
                        <p className="mt-2 text-xs text-slate-500">
                            Title: {browser?.page_title ?? "—"} · Studio:{" "}
                            {browser ? (browser.in_studio ? "yes" : "no") : "—"}
                        </p>
                    </CardContent>
                </Card>
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Raw JSON</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <pre className="max-h-[220px] overflow-auto rounded-md border border-slate-800 bg-slate-900/50 p-3 font-mono text-xs text-slate-400">
                            {health && browser
                                ? JSON.stringify({ health, browser_status: browser }, null, 2)
                                : loading
                                  ? "…"
                                  : error ?? "—"}
                        </pre>
                        {updated && <p className="mt-2 text-xs text-slate-500">Last fetch: {updated}</p>}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
