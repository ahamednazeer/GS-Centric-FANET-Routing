'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { ShieldCheck } from '@phosphor-icons/react';

export default function SecurityPage() {
    const [events, setEvents] = useState<any[]>([]);

    useEffect(() => {
        api.getEvents().then((data) => {
            const filtered = (data || []).filter((event: any) =>
                String(event.event_type).includes('FLOOD') || String(event.event_type).includes('REPLAY')
            );
            setEvents(filtered);
        }).catch(console.error);
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3">
                <ShieldCheck size={22} className="text-blue-400" />
                <h2 className="text-xl font-chivo uppercase tracking-wider">Security & Integrity</h2>
            </div>

            <div className="bg-slate-900/70 border border-slate-700 rounded-sm p-6 space-y-3 text-sm">
                <p className="text-slate-400 font-mono uppercase tracking-wider text-xs">Active Controls</p>
                <ul className="text-slate-300 space-y-2">
                    <li>HMAC-based flood authentication</li>
                    <li>Replay protection via sequence tracking</li>
                    <li>Lightweight payload encryption on data packets</li>
                </ul>
            </div>

            <div>
                <h3 className="text-sm uppercase tracking-wider font-mono text-slate-400 mb-3">Security Events</h3>
                <DataTable
                    data={events}
                    columns={[
                        { key: 'timestamp', label: 'Time' },
                        { key: 'node_id', label: 'Node' },
                        { key: 'event_type', label: 'Type' },
                        { key: 'message', label: 'Message' },
                    ]}
                    emptyMessage="No security events logged"
                />
            </div>
        </div>
    );
}
