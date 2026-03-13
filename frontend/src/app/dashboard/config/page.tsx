'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Sliders } from '@phosphor-icons/react';

export default function ConfigPage() {
    const [config, setConfig] = useState<any>(null);
    const [assumptions, setAssumptions] = useState<any>(null);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        Promise.all([api.getConfig(), api.getAssumptions()])
            .then(([cfg, assumptions]) => {
                setConfig(cfg);
                setAssumptions(assumptions);
            })
            .catch(console.error);
    }, []);

    const updateField = (key: string, value: string) => {
        setConfig({ ...config, [key]: Number(value) });
    };

    const save = async () => {
        if (!config) return;
        setSaving(true);
        try {
            await api.updateConfig({
                flood_interval_seconds: config.flood_interval_seconds,
                route_expiry_seconds: config.route_expiry_seconds,
                buffer_timeout_seconds: config.buffer_timeout_seconds,
                satellite_activation_delay_seconds: config.satellite_activation_delay_seconds,
                flood_ttl: config.flood_ttl,
                max_hops: config.max_hops,
                retry_interval_seconds: config.retry_interval_seconds,
                buffer_max_size: config.buffer_max_size,
                buffer_high_watermark: config.buffer_high_watermark,
                buffer_emergency_watermark: config.buffer_emergency_watermark,
                neighbor_min_threshold: config.neighbor_min_threshold,
            });
        } catch (err) {
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    if (!config) {
        return <div className="text-slate-500 font-mono">Loading configuration...</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3">
                <Sliders size={22} className="text-blue-400" />
                <h2 className="text-xl font-chivo uppercase tracking-wider">System Configuration</h2>
            </div>

            <div className="bg-slate-900/70 border border-slate-700 rounded-sm p-6 space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                    {[
                        ['flood_interval_seconds', 'Flood Interval (s)'],
                        ['route_expiry_seconds', 'Route Expiry (s)'],
                        ['buffer_timeout_seconds', 'Buffer Timeout (s)'],
                        ['satellite_activation_delay_seconds', 'Satellite Delay (s)'],
                        ['flood_ttl', 'Flood TTL'],
                        ['max_hops', 'Max Hops'],
                        ['retry_interval_seconds', 'Retry Interval (s)'],
                        ['buffer_max_size', 'Buffer Max Size'],
                        ['buffer_high_watermark', 'Buffer High Watermark'],
                        ['buffer_emergency_watermark', 'Buffer Emergency Watermark'],
                        ['neighbor_min_threshold', 'Neighbor Min Threshold'],
                    ].map(([key, label]) => (
                        <div key={key}>
                            <label className="block text-xs uppercase tracking-wider font-mono text-slate-400 mb-2">
                                {label}
                            </label>
                            <input
                                className="input-modern"
                                value={config[key] ?? ''}
                                onChange={(e) => updateField(key, e.target.value)}
                            />
                        </div>
                    ))}
                </div>
                <button className="btn-primary" onClick={save} disabled={saving}>
                    {saving ? 'Saving...' : 'Save Configuration'}
                </button>
            </div>

            {assumptions && (
                <div className="bg-slate-900/70 border border-slate-700 rounded-sm p-6 text-sm">
                    <p className="text-xs uppercase tracking-wider font-mono text-slate-400 mb-4">Network Assumptions</p>
                    <div className="grid md:grid-cols-2 gap-4 text-slate-300">
                        <div>Mobility Speed Range: {assumptions.mobility_speed_range_mps?.join(' - ')} m/s</div>
                        <div>Avg Radio Range: {assumptions.avg_radio_range_m} m</div>
                        <div>Channel Bandwidth: {assumptions.channel_bandwidth_mbps} Mbps</div>
                        <div>Expected Node Density: {assumptions.expected_node_density}</div>
                        <div>Expected GS Distance: {assumptions.expected_gs_distance_m} m</div>
                    </div>
                </div>
            )}
        </div>
    );
}
