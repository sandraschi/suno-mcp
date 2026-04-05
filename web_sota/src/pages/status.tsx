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

export function Status() {
    const [health, setHealth] = useState<HealthPayload | null>(null);
    const [browser, setBrowser] = useState<StatusPayload | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [h, s] = await Promise.all([fetchHealth(), fetchBrowserStatus()]);
            setHealth(h);
            setBrowser(s);
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
                    <h2 className="text-2xl font-bold tracking-tight text-white">Server status</h2>
                    <p className="text-slate-400">
                        Live data from <code className="text-slate-300">{getApiBase()}</code> — no fake CPU/RAM
                        numbers.
                    </p>
                </div>
                <Button variant="outline" size="sm" onClick={() => void load()} disabled={loading}>
                    {loading ? "Refreshing…" : "Refresh"}
                </Button>
            </div>

            {error && (
                <div className="rounded-md border border-amber-900/80 bg-amber-950/40 px-4 py-3 text-sm text-amber-100">
                    <strong className="text-amber-50">Backend unreachable.</strong> {error}
                </div>
            )}

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Health</CardTitle>
                        <Shield className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{health?.status ?? "—"}</div>
                        <p className="text-xs text-slate-400">v{health?.version ?? "—"}</p>
                    </CardContent>
                </Card>
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Uptime</CardTitle>
                        <Activity className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {health != null ? formatUptime(health.uptime) : "—"}
                        </div>
                        <p className="text-xs text-slate-400">seconds from /health</p>
                    </CardContent>
                </Card>
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Tools</CardTitle>
                        <Wrench className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{health?.tools_loaded ?? "—"}</div>
                        <p className="text-xs text-slate-400">tools_loaded</p>
                    </CardContent>
                </Card>
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Mode</CardTitle>
                        <Globe className="h-4 w-4 text-orange-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{browser?.server_mode ?? "—"}</div>
                        <p className="text-xs text-slate-400">from /api/v1/status</p>
                    </CardContent>
                </Card>
            </div>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="text-white">Playwright / Suno page (same process as MCP tools)</CardTitle>
                </CardHeader>
                <CardContent>
                    <dl className="grid gap-2 font-mono text-sm text-slate-300 md:grid-cols-2">
                        <div className="flex justify-between border-b border-slate-800 py-1">
                            <span className="text-slate-500">browser_open</span>
                            <span>{browser ? String(browser.browser_open) : "—"}</span>
                        </div>
                        <div className="flex justify-between border-b border-slate-800 py-1">
                            <span className="text-slate-500">page_ready</span>
                            <span>{browser ? String(browser.page_ready) : "—"}</span>
                        </div>
                        <div className="flex justify-between border-b border-slate-800 py-1 md:col-span-2">
                            <span className="text-slate-500">current_url</span>
                            <span className="max-w-[70%] break-all text-right">{browser?.current_url ?? "—"}</span>
                        </div>
                        <div className="flex justify-between border-b border-slate-800 py-1 md:col-span-2">
                            <span className="text-slate-500">page_title</span>
                            <span className="max-w-[70%] break-all text-right">{browser?.page_title ?? "—"}</span>
                        </div>
                        <div className="flex justify-between border-b border-slate-800 py-1">
                            <span className="text-slate-500">in_studio</span>
                            <span>{browser ? String(browser.in_studio) : "—"}</span>
                        </div>
                    </dl>
                </CardContent>
            </Card>
        </div>
    );
}
