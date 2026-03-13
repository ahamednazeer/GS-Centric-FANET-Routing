'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { Stack } from '@phosphor-icons/react';

export default function BufferPage() {
    const [buffer, setBuffer] = useState<any[]>([]);

    const load = async () => {
        const data = await api.getBuffer();
        setBuffer(data || []);
    };

    useEffect(() => {
        load().catch(console.error);
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-chivo uppercase tracking-wider flex items-center gap-3">
                    <Stack size={22} className="text-blue-400" /> Buffer Queue
                </h2>
                <button
                    onClick={() => load().catch(console.error)}
                    className="text-xs uppercase tracking-wider font-mono px-3 py-2 rounded-sm border border-slate-700 hover:border-blue-500"
                >
                    Refresh
                </button>
            </div>
            <DataTable
                data={buffer}
                columns={[
                    { key: 'node_id', label: 'Node' },
                    { key: 'packet_id', label: 'Packet' },
                    { key: 'priority', label: 'Priority' },
                    { key: 'retry_count', label: 'Retries' },
                    { key: 'expiry_time', label: 'Expiry' },
                ]}
                emptyMessage="No buffered packets"
            />
        </div>
    );
}
