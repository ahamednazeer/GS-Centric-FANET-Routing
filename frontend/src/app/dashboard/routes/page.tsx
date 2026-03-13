'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { FlowArrow } from '@phosphor-icons/react';

export default function RoutesPage() {
    const [routes, setRoutes] = useState<any[]>([]);

    const load = async () => {
        const data = await api.getRoutes();
        setRoutes(data || []);
    };

    useEffect(() => {
        load().catch(console.error);
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-chivo uppercase tracking-wider flex items-center gap-3">
                    <FlowArrow size={22} className="text-blue-400" /> Route Cache
                </h2>
                <button
                    onClick={() => load().catch(console.error)}
                    className="text-xs uppercase tracking-wider font-mono px-3 py-2 rounded-sm border border-slate-700 hover:border-blue-500"
                >
                    Refresh
                </button>
            </div>
            <DataTable
                data={routes}
                columns={[
                    { key: 'node_id', label: 'Node' },
                    { key: 'gs_id', label: 'GS' },
                    { key: 'next_hop_id', label: 'Next Hop' },
                    { key: 'hop_count', label: 'Hops' },
                    { key: 'route_confidence', label: 'Confidence' },
                    { key: 'link_quality_score', label: 'Link' },
                    { key: 'last_updated', label: 'Updated' },
                ]}
                emptyMessage="No routes cached"
            />
        </div>
    );
}
