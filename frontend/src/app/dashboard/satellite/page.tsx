'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DataTable from '@/components/DataTable';
import StatusBadge from '@/components/StatusBadge';
import { Radio } from '@phosphor-icons/react';

export default function SatellitePage() {
    const [states, setStates] = useState<any[]>([]);

    const load = async () => {
        const data = await api.getSatelliteStates();
        setStates(data || []);
    };

    useEffect(() => {
        load().catch(console.error);
    }, []);

    const rows = states.map((state) => ({
        ...state,
        id: state.node_id ?? state.id,
    }));
    const isEmpty = rows.length === 0;

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3">
                <Radio size={22} className="text-blue-400" />
                <h2 className="text-xl font-chivo uppercase tracking-wider">Satellite Fallback</h2>
            </div>

            <div className="bg-slate-900/70 border border-slate-700 rounded-sm p-6 text-sm space-y-2">
                <p className="text-slate-400 font-mono uppercase tracking-wider text-xs">Activation Rules</p>
                <p className="text-slate-300">Triggered when floods expire, routes are absent, and neighbor count drops below threshold.</p>
                <p className="text-slate-500">Emergency data only, compressed and batch transmitted.</p>
            </div>

            {isEmpty ? (
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-8">
                    <div className="flex items-center gap-3">
                        <div className="border border-slate-700/70 bg-slate-950/60 rounded-sm p-2">
                            <Radio size={18} className="text-blue-400" />
                        </div>
                        <div>
                            <p className="text-xs uppercase tracking-wider font-mono text-slate-400">Current State</p>
                            <p className="text-lg font-chivo uppercase tracking-wider text-slate-100">Idle (No Activations)</p>
                        </div>
                    </div>
                    <p className="text-sm text-slate-400 mt-3">
                        No nodes are in satellite mode right now. This is expected during stable routing. If floods expire,
                        routes are absent, and neighbor count drops below the threshold, activations will appear here.
                    </p>
                    <div className="mt-4 grid gap-3 sm:grid-cols-2 text-xs font-mono text-slate-300">
                        <div className="bg-slate-950/60 border border-slate-800/70 rounded-sm p-3 space-y-1">
                            <p className="text-slate-500 uppercase tracking-wider">What shows up</p>
                            <p>Node ID, activation time, last switch, and usage rate.</p>
                        </div>
                        <div className="bg-slate-950/60 border border-slate-800/70 rounded-sm p-3 space-y-1">
                            <p className="text-slate-500 uppercase tracking-wider">Activation trigger</p>
                            <p>Floods expire + no valid routes + low neighbor count.</p>
                        </div>
                    </div>
                </div>
            ) : (
                <DataTable
                    data={rows}
                    columns={[
                        { key: 'node_id', label: 'Node' },
                        {
                            key: 'active',
                            label: 'Status',
                            render: (item: any) => <StatusBadge status={item.active ? 'ACTIVE' : 'INACTIVE'} />,
                        },
                        { key: 'activated_at', label: 'Activated At' },
                        { key: 'last_switch', label: 'Last Switch' },
                        { key: 'usage_rate', label: 'Usage' },
                    ]}
                    emptyMessage="No satellite activations"
                />
            )}
        </div>
    );
}
