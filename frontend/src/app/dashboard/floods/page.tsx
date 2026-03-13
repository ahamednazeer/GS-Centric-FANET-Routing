'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { Broadcast } from '@phosphor-icons/react';

export default function FloodsPage() {
    const [gsId, setGsId] = useState('GS-CORE');
    const [ttl, setTtl] = useState<number | ''>('');
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const emit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const data = await api.emitFlood(gsId, ttl === '' ? undefined : Number(ttl));
            setResult(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3">
                <Broadcast size={22} className="text-blue-400" />
                <h2 className="text-xl font-chivo uppercase tracking-wider">GS Flood Operations</h2>
            </div>

            <form onSubmit={emit} className="bg-slate-900/70 border border-slate-700 rounded-sm p-6 space-y-4">
                <div>
                    <label className="block text-xs uppercase tracking-wider font-mono text-slate-400 mb-2">GS ID</label>
                    <input
                        className="input-modern"
                        value={gsId}
                        onChange={(e) => setGsId(e.target.value)}
                        placeholder="GS-CORE"
                    />
                </div>
                <div>
                    <label className="block text-xs uppercase tracking-wider font-mono text-slate-400 mb-2">Flood TTL</label>
                    <input
                        className="input-modern"
                        value={ttl}
                        onChange={(e) => setTtl(e.target.value === '' ? '' : Number(e.target.value))}
                        placeholder="Leave empty for default"
                    />
                </div>
                <button
                    type="submit"
                    className="btn-primary"
                    disabled={loading}
                >
                    {loading ? 'Broadcasting...' : 'Emit Flood'}
                </button>
            </form>

            {result && (
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-sm p-5 text-sm">
                    <p className="text-slate-400 font-mono uppercase tracking-wider text-xs mb-3">Flood Result</p>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <p className="text-slate-500 text-xs uppercase tracking-wider">Sequence</p>
                            <p className="text-slate-100 font-mono text-lg">{result.flood_sequence_number}</p>
                        </div>
                        <div>
                            <p className="text-slate-500 text-xs uppercase tracking-wider">Propagated</p>
                            <p className="text-slate-100 font-mono text-lg">{result.propagated_nodes}</p>
                        </div>
                        <div>
                            <p className="text-slate-500 text-xs uppercase tracking-wider">Accepted</p>
                            <p className="text-slate-100 font-mono text-lg">{result.accepted_nodes}</p>
                        </div>
                        <div>
                            <p className="text-slate-500 text-xs uppercase tracking-wider">Dropped</p>
                            <p className="text-slate-100 font-mono text-lg">{result.dropped_nodes}</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
