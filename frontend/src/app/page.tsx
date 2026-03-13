'use client';

import React, { useState } from 'react';
import { Airplane, Radio, Broadcast, ShieldCheck } from '@phosphor-icons/react';
import { api } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function LandingPage() {
    const router = useRouter();
    const [nodeId, setNodeId] = useState('UAV-01');
    const [role, setRole] = useState<'GS' | 'UAV'>('UAV');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleConnect = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await api.registerNode(nodeId, role);
            localStorage.setItem('fanet_node_id', nodeId);
            localStorage.setItem('fanet_role', role);
            router.push('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Failed to register node');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div
            className="min-h-screen flex items-center justify-center bg-cover bg-center relative"
            style={{ backgroundImage: 'linear-gradient(to bottom right, #0f172a, #1e293b)' }}
        >
            <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" />
            <div className="scanlines" />

            <div className="relative z-10 w-full max-w-5xl mx-4 grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
                <div className="bg-slate-900/70 border border-slate-700 rounded-sm p-8 backdrop-blur-md">
                    <div className="flex items-center gap-3 mb-6">
                        <Radio size={36} weight="duotone" className="text-blue-400" />
                        <div>
                            <h1 className="text-3xl font-chivo font-bold uppercase tracking-wider">GS-Centric FANET</h1>
                            <p className="text-slate-400 text-sm">Directed uplink routing command layer</p>
                        </div>
                    </div>

                    <p className="text-slate-300 leading-relaxed mb-6">
                        This system prioritizes GS-directed uplink reliability with continuous, GS-rooted routing trees.
                        No peer-to-peer optimization, no symmetric assumptions, and no route discovery storms.
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="card">
                            <div className="flex items-center gap-3 mb-2">
                                <Broadcast size={22} className="text-blue-400" />
                                <h3 className="text-sm uppercase tracking-wider font-mono text-slate-300">Flood Control</h3>
                            </div>
                            <p className="text-xs text-slate-500">Adaptive GS flooding, suppression jitter, and TTL-aware propagation.</p>
                        </div>
                        <div className="card">
                            <div className="flex items-center gap-3 mb-2">
                                <Airplane size={22} className="text-emerald-400" />
                                <h3 className="text-sm uppercase tracking-wider font-mono text-slate-300">Mobility Intelligence</h3>
                            </div>
                            <p className="text-xs text-slate-500">Link stability scoring, route confidence, and partition detection.</p>
                        </div>
                        <div className="card">
                            <div className="flex items-center gap-3 mb-2">
                                <ShieldCheck size={22} className="text-amber-400" />
                                <h3 className="text-sm uppercase tracking-wider font-mono text-slate-300">Integrity</h3>
                            </div>
                            <p className="text-xs text-slate-500">HMAC flood validation, replay protection, and lightweight encryption.</p>
                        </div>
                        <div className="card">
                            <div className="flex items-center gap-3 mb-2">
                                <Radio size={22} className="text-purple-400" />
                                <h3 className="text-sm uppercase tracking-wider font-mono text-slate-300">Satellite Fallback</h3>
                            </div>
                            <p className="text-xs text-slate-500">Partition-aware activation with compression and traffic shaping.</p>
                        </div>
                    </div>
                </div>

                <div className="bg-slate-900/90 border border-slate-700 rounded-sm p-8 backdrop-blur-md">
                    <h2 className="text-xl font-chivo font-bold uppercase tracking-wider mb-4">Connect Node</h2>

                    {error && (
                        <div className="bg-red-950/50 border border-red-800 rounded-sm p-3 mb-4 text-sm text-red-400">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleConnect} className="space-y-5">
                        <div>
                            <label className="block text-slate-400 text-xs uppercase tracking-wider mb-2 font-mono">
                                Node ID
                            </label>
                            <input
                                type="text"
                                value={nodeId}
                                onChange={(e) => setNodeId(e.target.value)}
                                required
                                className="w-full bg-slate-950 border-slate-700 text-slate-100 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-sm placeholder:text-slate-600 font-mono text-sm px-3 py-2.5 border outline-none"
                                placeholder="UAV-01"
                                disabled={loading}
                            />
                        </div>

                        <div>
                            <label className="block text-slate-400 text-xs uppercase tracking-wider mb-2 font-mono">
                                Role
                            </label>
                            <div className="grid grid-cols-2 gap-3">
                                {(['UAV', 'GS'] as const).map((option) => (
                                    <button
                                        type="button"
                                        key={option}
                                        onClick={() => setRole(option)}
                                        className={`border rounded-sm px-4 py-3 text-sm uppercase tracking-wider font-mono transition-all ${
                                            role === option
                                                ? 'border-blue-400 text-blue-300 bg-blue-950/40'
                                                : 'border-slate-700 text-slate-400 hover:border-slate-500'
                                        }`}
                                    >
                                        {option}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-sm px-4 py-3 shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Connecting...' : 'Launch Console'}
                        </button>
                    </form>

                    <div className="mt-6 border border-slate-800 rounded-sm p-4 bg-slate-950/50">
                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-2 font-mono">Quick Profiles</p>
                        <div className="grid grid-cols-2 gap-3 text-xs font-mono text-slate-400">
                            <button
                                type="button"
                                onClick={() => {
                                    setNodeId('GS-CORE');
                                    setRole('GS');
                                }}
                                className="text-left hover:text-slate-200 transition"
                            >
                                GS Core / GS
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setNodeId('UAV-ALPHA');
                                    setRole('UAV');
                                }}
                                className="text-left hover:text-slate-200 transition"
                            >
                                UAV Alpha / UAV
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
