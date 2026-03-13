'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { ActivityIcon } from '@phosphor-icons/react';
import { DataCard } from '@/components/DataCard';

export default function TelemetryPage() {
    const [summary, setSummary] = useState<any>(null);
    const [counters, setCounters] = useState<any>(null);

    useEffect(() => {
        Promise.all([api.getMetricsSummary(), api.getMetricsCounters()])
            .then(([summaryData, counterData]) => {
                setSummary(summaryData);
                setCounters(counterData);
            })
            .catch(console.error);
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3">
                <ActivityIcon size={22} className="text-blue-400" />
                <h2 className="text-xl font-chivo uppercase tracking-wider">Telemetry</h2>
            </div>

            <div className="grid gap-4 md:grid-cols-4">
                <DataCard title="Total Packets" value={summary?.total_packets ?? '--'} />
                <DataCard title="Delivered" value={summary?.delivered ?? '--'} />
                <DataCard title="Buffered" value={summary?.buffered ?? '--'} />
                <DataCard title="Dropped" value={summary?.dropped ?? '--'} />
            </div>

            <div className="bg-slate-900/70 border border-slate-700 rounded-sm p-6 text-sm">
                <p className="text-xs uppercase tracking-wider font-mono text-slate-400 mb-3">Counters</p>
                <div className="grid grid-cols-2 gap-4 text-slate-300">
                    {counters &&
                        Object.entries(counters).map(([key, value]) => (
                            <div key={key} className="flex items-center justify-between">
                                <span className="text-slate-500 font-mono text-xs uppercase tracking-wider">{key}</span>
                                <span className="font-mono text-sm">{value as any}</span>
                            </div>
                        ))}
                </div>
            </div>
        </div>
    );
}
