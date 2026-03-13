'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { DataCard } from '@/components/DataCard';
import DataTable from '@/components/DataTable';
import StatusBadge from '@/components/StatusBadge';
import {
    Gauge,
    Broadcast,
    Stack,
    FlowArrow,
    ActivityIcon,
    Radio,
} from '@phosphor-icons/react';

interface RouteEntry {
    id: number;
    node_id: string;
    gs_id: string;
    next_hop_id: string;
    hop_count: number;
    route_confidence: number;
    link_quality_score: number;
    last_updated: string;
    expires_at: string;
}

interface EventLog {
    id: number;
    timestamp: string;
    node_id?: string;
    event_type: string;
    message: string;
}

export default function DashboardOverview() {
    const [metrics, setMetrics] = useState<any>(null);
    const [health, setHealth] = useState<any>(null);
    const [routes, setRoutes] = useState<RouteEntry[]>([]);
    const [events, setEvents] = useState<EventLog[]>([]);
    const [config, setConfig] = useState<any>(null);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [seedForm, setSeedForm] = useState({
        gs_id: 'GS-CORE',
        uav_count: 12,
        uav_prefix: 'UAV',
        neighbor_degree: 2,
        topology: 'ring',
        reset: true,
        auto_flood: true,
        auto_data: true,
        sample_packets: 4,
    });
    const [simForm, setSimForm] = useState({
        gs_id: 'GS-CORE',
        duration_seconds: 0,
        tick_interval_seconds: 2,
        flood_interval_seconds: 10,
        data_interval_seconds: 5,
        uav_count: 12,
        uav_prefix: 'UAV',
        neighbor_degree: 2,
        topology: 'ring',
        reset: false,
        auto_flood: true,
        auto_data: true,
        sample_packets: 4,
    });
    const [simStatus, setSimStatus] = useState<any>(null);
    const [nowTs, setNowTs] = useState(Date.now());
    const [seeding, setSeeding] = useState(false);

    const load = useCallback(async () => {
        try {
            const [metricsSummary, healthSnapshot, routeTable, eventLog, configData] = await Promise.all([
                api.getMetricsSummary(),
                api.getHealth(),
                api.getRoutes(),
                api.getEvents(),
                api.getConfig(),
            ]);
            setMetrics(metricsSummary);
            setHealth(healthSnapshot);
            setRoutes(routeTable || []);
            setEvents(eventLog || []);
            setConfig(configData);
            const status = await api.simulateStatus().catch(() => null);
            setSimStatus(status);
        } catch (err) {
            console.error('Failed to load dashboard', err);
        }
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    useEffect(() => {
        if (!autoRefresh) return;
        const refreshMs = simStatus?.running ? 2000 : 10000;
        const interval = setInterval(() => {
            load();
        }, refreshMs);
        return () => clearInterval(interval);
    }, [autoRefresh, load, simStatus?.running]);

    useEffect(() => {
        const interval = setInterval(async () => {
            const status = await api.simulateStatus().catch(() => null);
            if (status) {
                setSimStatus(status);
            }
        }, simStatus?.running ? 2000 : 5000);
        return () => clearInterval(interval);
    }, [simStatus?.running]);

    useEffect(() => {
        if (simStatus?.running) {
            setAutoRefresh(true);
        }
    }, [simStatus?.running]);

    useEffect(() => {
        if (!simStatus?.running) return;
        const interval = setInterval(() => {
            setNowTs(Date.now());
        }, 1000);
        return () => clearInterval(interval);
    }, [simStatus?.running]);

    useEffect(() => {
        setSimForm((prev) => ({
            ...prev,
            gs_id: seedForm.gs_id,
            uav_count: seedForm.uav_count,
            uav_prefix: seedForm.uav_prefix,
            neighbor_degree: seedForm.neighbor_degree,
            topology: seedForm.topology,
        }));
    }, [
        seedForm.gs_id,
        seedForm.uav_count,
        seedForm.uav_prefix,
        seedForm.neighbor_degree,
        seedForm.topology,
    ]);

    const seed = async (e: React.FormEvent) => {
        e.preventDefault();
        setSeeding(true);
        try {
            await api.seedSimulation(seedForm);
            await load();
        } catch (err) {
            console.error(err);
        } finally {
            setSeeding(false);
        }
    };

    const startSimulation = async () => {
        try {
            const status = await api.simulateRun({
                ...simForm,
                gs_id: seedForm.gs_id,
                uav_count: seedForm.uav_count,
                uav_prefix: seedForm.uav_prefix,
                neighbor_degree: seedForm.neighbor_degree,
                topology: seedForm.topology,
            });
            setSimStatus(status);
        } catch (err) {
            console.error(err);
        }
    };

    const stopSimulation = async () => {
        try {
            const status = await api.simulateStop();
            setSimStatus(status);
        } catch (err) {
            console.error(err);
        }
    };

    const simConfig = simStatus?.config ?? simForm;
    const formatTs = (value: string | null | undefined) => {
        if (!value) return '--';
        const parsed = Date.parse(value);
        if (Number.isNaN(parsed)) return value;
        return new Date(parsed).toLocaleTimeString();
    };

    const getProgress = (last: string | null | undefined, intervalSeconds: number) => {
        if (!intervalSeconds || intervalSeconds <= 0) {
            return { progress: 0, remaining: null, due: false, hasSignal: false };
        }
        if (!last) {
            return { progress: 0, remaining: intervalSeconds, due: false, hasSignal: false };
        }
        const lastTs = Date.parse(last);
        if (Number.isNaN(lastTs)) {
            return { progress: 0, remaining: intervalSeconds, due: false, hasSignal: false };
        }
        const intervalMs = intervalSeconds * 1000;
        const elapsed = Math.max(0, nowTs - lastTs);
        const progress = Math.min(1, elapsed / intervalMs);
        const remaining = Math.max(0, intervalMs - elapsed) / 1000;
        return { progress, remaining, due: remaining <= 0, hasSignal: true };
    };

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h2 className="text-2xl font-chivo font-bold uppercase tracking-wider flex items-center gap-3">
                        <Gauge size={26} weight="duotone" className="text-blue-400" />
                        Network Overview
                    </h2>
                    <p className="text-slate-500 mt-1">Directed GS routing with adaptive flooding and buffering.</p>
                </div>
                <button
                    onClick={() => api.tick()}
                    className="bg-slate-800/60 border border-slate-700 text-slate-200 px-4 py-2 rounded-sm text-xs uppercase tracking-wider font-mono hover:border-blue-500 transition"
                >
                    Run Tick
                </button>
            </div>

            <div className="bg-slate-900/70 border border-slate-700 rounded-sm p-6 space-y-4">
                <div className="flex items-center justify-between gap-4 flex-wrap">
                    <div>
                        <p className="text-xs uppercase tracking-wider font-mono text-slate-400">Step 1 — Seed Network</p>
                        <p className="text-slate-500 text-sm">Create nodes + neighbor graph for the scenario.</p>
                    </div>
                    <button
                        onClick={() => setAutoRefresh((prev) => !prev)}
                        className="text-xs uppercase tracking-wider font-mono px-3 py-2 rounded-sm border border-slate-700 hover:border-blue-500"
                    >
                        {autoRefresh ? 'Auto Refresh: On' : 'Auto Refresh: Off'}
                    </button>
                </div>

                <form onSubmit={seed} className="grid gap-4 md:grid-cols-5">
                    <div>
                        <label className="block text-xs uppercase tracking-wider font-mono text-slate-400 mb-2">GS ID</label>
                        <input
                            className="input-modern"
                            value={seedForm.gs_id}
                            onChange={(e) => setSeedForm({ ...seedForm, gs_id: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="block text-xs uppercase tracking-wider font-mono text-slate-400 mb-2">UAV Count</label>
                        <input
                            className="input-modern"
                            type="number"
                            value={seedForm.uav_count}
                            onChange={(e) => setSeedForm({ ...seedForm, uav_count: Number(e.target.value) })}
                        />
                    </div>
                    <div>
                        <label className="block text-xs uppercase tracking-wider font-mono text-slate-400 mb-2">UAV Prefix</label>
                        <input
                            className="input-modern"
                            value={seedForm.uav_prefix}
                            onChange={(e) => setSeedForm({ ...seedForm, uav_prefix: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="block text-xs uppercase tracking-wider font-mono text-slate-400 mb-2">Neighbor Degree</label>
                        <input
                            className="input-modern"
                            type="number"
                            value={seedForm.neighbor_degree}
                            onChange={(e) => setSeedForm({ ...seedForm, neighbor_degree: Number(e.target.value) })}
                        />
                    </div>
                    <div>
                        <label className="block text-xs uppercase tracking-wider font-mono text-slate-400 mb-2">Topology</label>
                        <input
                            className="input-modern"
                            value={seedForm.topology}
                            onChange={(e) => setSeedForm({ ...seedForm, topology: e.target.value })}
                        />
                    </div>
                    <div className="flex items-end gap-3">
                        <button type="submit" className="btn-primary" disabled={seeding}>
                            {seeding ? 'Seeding...' : 'Seed'}
                        </button>
                    </div>
                </form>

                <div className="flex flex-wrap items-center gap-6 text-xs uppercase tracking-wider font-mono text-slate-400">
                    <label className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={seedForm.reset}
                            onChange={(e) => setSeedForm({ ...seedForm, reset: e.target.checked })}
                        />
                        Reset
                    </label>
                    <label className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={seedForm.auto_flood}
                            onChange={(e) => setSeedForm({ ...seedForm, auto_flood: e.target.checked })}
                        />
                        Auto Flood
                    </label>
                    <label className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={seedForm.auto_data}
                            onChange={(e) => setSeedForm({ ...seedForm, auto_data: e.target.checked })}
                        />
                        Sample Traffic
                    </label>
                    <div className="flex items-center gap-2">
                        <span>Samples</span>
                        <input
                            className="input-modern w-20"
                            type="number"
                            value={seedForm.sample_packets}
                            onChange={(e) => setSeedForm({ ...seedForm, sample_packets: Number(e.target.value) })}
                        />
                    </div>
                </div>
            </div>

            <div className="bg-slate-900/70 border border-slate-700 rounded-sm p-6 space-y-4">
                <div className="flex items-center justify-between flex-wrap gap-4">
                    <div>
                        <p className="text-xs uppercase tracking-wider font-mono text-slate-400">Step 2 — Run Simulation</p>
                        <p className="text-slate-500 text-sm">Runs floods + data + ticks using the seed settings above.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={startSimulation}
                            className="btn-primary"
                        >
                            Start
                        </button>
                        <button
                            onClick={stopSimulation}
                            className="btn-secondary"
                        >
                            Stop
                        </button>
                    </div>
                </div>

                <div className="text-xs uppercase tracking-wider font-mono text-slate-500">
                    Using: {seedForm.gs_id} • {seedForm.uav_count} UAVs • {seedForm.topology} topology
                </div>

                <div className="grid gap-4 md:grid-cols-4">
                    {[
                        ['duration_seconds', 'Duration (s)'],
                        ['tick_interval_seconds', 'Tick Interval (s)'],
                        ['flood_interval_seconds', 'Flood Interval (s)'],
                        ['data_interval_seconds', 'Data Interval (s)'],
                        ['sample_packets', 'Sample Packets'],
                    ].map(([key, label]) => (
                        <div key={key}>
                            <label className="block text-xs uppercase tracking-wider font-mono text-slate-400 mb-2">{label}</label>
                            <input
                                className="input-modern"
                                type="number"
                                value={(simForm as any)[key]}
                                onChange={(e) => setSimForm({ ...simForm, [key]: Number(e.target.value) })}
                            />
                        </div>
                    ))}
                </div>

                <div className="flex flex-wrap items-center gap-6 text-xs uppercase tracking-wider font-mono text-slate-400">
                    <label className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={simForm.reset}
                            onChange={(e) => setSimForm({ ...simForm, reset: e.target.checked })}
                        />
                        Reset on Start
                    </label>
                    <label className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={simForm.auto_flood}
                            onChange={(e) => setSimForm({ ...simForm, auto_flood: e.target.checked })}
                        />
                        Auto Flood
                    </label>
                    <label className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={simForm.auto_data}
                            onChange={(e) => setSimForm({ ...simForm, auto_data: e.target.checked })}
                        />
                        Auto Data
                    </label>
                </div>

                {simStatus && (
                    <div className="bg-slate-950/60 border border-slate-800 rounded-sm p-4 text-sm text-slate-300">
                        <div className="grid md:grid-cols-4 gap-4">
                            <div>
                                <p className="text-xs uppercase tracking-wider font-mono text-slate-500">Status</p>
                                <div className="flex items-center gap-2">
                                    <span className={`w-2.5 h-2.5 rounded-full ${simStatus.running ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
                                    <p className="text-sm">{simStatus.running ? 'RUNNING' : 'STOPPED'}</p>
                                </div>
                            </div>
                            <div>
                                <p className="text-xs uppercase tracking-wider font-mono text-slate-500">Elapsed</p>
                                <p className="text-sm">{Math.round(simStatus.elapsed_seconds || 0)}s</p>
                            </div>
                            <div>
                                <p className="text-xs uppercase tracking-wider font-mono text-slate-500">Ticks</p>
                                <p className="text-sm">{simStatus.ticks ?? 0}</p>
                            </div>
                            <div>
                                <p className="text-xs uppercase tracking-wider font-mono text-slate-500">Last Tick</p>
                                <p className="text-sm">{formatTs(simStatus.last_tick_at)}</p>
                            </div>
                        </div>
                    </div>
                )}

                {simStatus?.running && (
                    <div className="bg-slate-950/60 border border-slate-800 rounded-sm p-4 text-sm text-slate-300">
                        <div className="flex items-center justify-between">
                            <p className="text-xs uppercase tracking-wider font-mono text-slate-500">Live Signals</p>
                            <span className="text-[10px] uppercase tracking-wider text-slate-500">Real-time cadence</span>
                        </div>
                        <div className="mt-4 space-y-3">
                            {[
                                ['Tick', simStatus.last_tick_at, Number(simConfig.tick_interval_seconds || 0), 'bg-blue-500/70'],
                                ['Flood', simStatus.last_flood_at, Number(simConfig.flood_interval_seconds || 0), 'bg-emerald-500/70'],
                                ['Data', simStatus.last_data_at, Number(simConfig.data_interval_seconds || 0), 'bg-amber-400/70'],
                            ].map(([label, last, interval, color]) => {
                                const { progress, remaining, due, hasSignal } = getProgress(last as string, interval as number);
                                const statusText = hasSignal
                                    ? due
                                        ? 'due now'
                                        : `${Math.ceil(remaining || 0)}s to next`
                                    : 'waiting';
                                return (
                                    <div key={label as string} className="space-y-1">
                                        <div className="flex items-center justify-between text-xs text-slate-400 font-mono uppercase tracking-wider">
                                            <span>{label}</span>
                                            <span>{statusText}</span>
                                        </div>
                                        <div className="h-2 w-full rounded-full bg-slate-800/80 overflow-hidden">
                                            <div
                                                className={`h-full ${color} transition-all duration-500`}
                                                style={{ width: `${Math.max(5, progress * 100)}%` }}
                                            />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                <DataCard
                    title="Active Nodes"
                    value={health?.nodes ?? '--'}
                    icon={Radio}
                    subtitle="Registered GS/UAV"
                />
                <DataCard
                    title="Routes Cached"
                    value={health?.routes ?? '--'}
                    icon={FlowArrow}
                    subtitle="GS-rooted paths"
                />
                <DataCard
                    title="Buffered Packets"
                    value={health?.buffered_packets ?? '--'}
                    icon={Stack}
                    subtitle="Store-carry-forward"
                />
            </div>

            <div className="grid gap-4 md:grid-cols-4">
                <DataCard
                    title="Delivered"
                    value={metrics?.delivered ?? '--'}
                    icon={Gauge}
                />
                <DataCard
                    title="Forwarded"
                    value={metrics?.forwarded ?? '--'}
                    icon={FlowArrow}
                />
                <DataCard
                    title="Dropped"
                    value={metrics?.dropped ?? '--'}
                    icon={Broadcast}
                />
                <DataCard
                    title="PDR"
                    value={metrics?.packet_delivery_ratio ?? '--'}
                    icon={ActivityIcon}
                />
            </div>

            <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
                <div>
                    <h3 className="text-sm uppercase tracking-wider font-mono text-slate-400 mb-3">Route Cache</h3>
                    <DataTable
                        data={routes}
                        columns={[
                            { key: 'node_id', label: 'Node' },
                            { key: 'gs_id', label: 'GS' },
                            { key: 'next_hop_id', label: 'Next Hop' },
                            { key: 'hop_count', label: 'Hops' },
                            {
                                key: 'route_confidence',
                                label: 'Confidence',
                                render: (item: RouteEntry) => `${(item.route_confidence * 100).toFixed(0)}%`,
                            },
                            {
                                key: 'link_quality_score',
                                label: 'Link',
                                render: (item: RouteEntry) => `${(item.link_quality_score * 100).toFixed(0)}%`,
                            },
                        ]}
                        emptyMessage="No routes cached yet"
                    />
                </div>
                <div>
                    <h3 className="text-sm uppercase tracking-wider font-mono text-slate-400 mb-3">System Config</h3>
                    <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-5 space-y-3 text-sm">
                        <div className="flex items-center justify-between">
                            <span className="text-slate-500 font-mono">Flood Interval</span>
                            <span className="text-slate-200">{config?.flood_interval_seconds ?? '--'}s</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-slate-500 font-mono">Route Expiry</span>
                            <span className="text-slate-200">{config?.route_expiry_seconds ?? '--'}s</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-slate-500 font-mono">Buffer Timeout</span>
                            <span className="text-slate-200">{config?.buffer_timeout_seconds ?? '--'}s</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-slate-500 font-mono">Satellite Delay</span>
                            <span className="text-slate-200">{config?.satellite_activation_delay_seconds ?? '--'}s</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-slate-500 font-mono">Flood TTL</span>
                            <span className="text-slate-200">{config?.flood_ttl ?? '--'} hops</span>
                        </div>
                    </div>
                </div>
            </div>

            <div>
                <h3 className="text-sm uppercase tracking-wider font-mono text-slate-400 mb-3">Recent Events</h3>
                <DataTable
                    data={events.map((event) => ({
                        ...event,
                        id: event.id,
                    }))}
                    columns={[
                        { key: 'timestamp', label: 'Time' },
                        { key: 'node_id', label: 'Node' },
                        { key: 'event_type', label: 'Type', render: (item: EventLog) => <StatusBadge status={item.event_type} /> },
                        { key: 'message', label: 'Message' },
                    ]}
                    emptyMessage="No events yet"
                />
            </div>
        </div>
    );
}
