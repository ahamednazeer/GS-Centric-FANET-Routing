'use client';

import React, { useEffect, useMemo, useRef, useState, useCallback, ReactNode } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
    Gauge,
    Broadcast,
    FlowArrow,
    Stack,
    ShieldCheck,
    Radio,
    ActivityIcon,
    Sliders,
    SignOut,
} from '@phosphor-icons/react';
import Link from 'next/link';

interface MenuItem {
    icon: React.ElementType;
    label: string;
    path: string;
}

interface FanetLayoutProps {
    children: ReactNode;
}

const COLLAPSED_WIDTH = 72;
const DEFAULT_WIDTH = 72;
const MAX_WIDTH = 320;
const LABEL_MIN_WIDTH = 180;

const menuItems: MenuItem[] = [
    { icon: Gauge, label: 'Overview', path: '/dashboard' },
    { icon: FlowArrow, label: 'Routes', path: '/dashboard/routes' },
    { icon: Stack, label: 'Buffer', path: '/dashboard/buffer' },
    { icon: Broadcast, label: 'Flood Ops', path: '/dashboard/floods' },
    { icon: ShieldCheck, label: 'Security', path: '/dashboard/security' },
    { icon: Radio, label: 'Satellite', path: '/dashboard/satellite' },
    { icon: ActivityIcon, label: 'Telemetry', path: '/dashboard/telemetry' },
    { icon: Sliders, label: 'Config', path: '/dashboard/config' },
];

export default function FanetLayout({ children }: FanetLayoutProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_WIDTH);
    const [isResizing, setIsResizing] = useState(false);
    const [isHidden, setIsHidden] = useState(false);
    const isCollapsed = isHidden || sidebarWidth < LABEL_MIN_WIDTH;
    const sidebarRef = useRef<HTMLDivElement>(null);
    const resizeFrame = useRef<number | null>(null);
    const resizeStartX = useRef(0);
    const resizeStartWidth = useRef(0);

    const nodeId = useMemo(() => (typeof window !== 'undefined' ? localStorage.getItem('fanet_node_id') : null), []);
    const role = useMemo(() => (typeof window !== 'undefined' ? localStorage.getItem('fanet_role') : null), []);

    useEffect(() => {
        const savedWidth = localStorage.getItem('sidebarWidth');
        const savedHidden = localStorage.getItem('sidebarHidden');
        if (savedWidth) {
            setSidebarWidth(parseInt(savedWidth));
        }
        if (savedHidden === 'true') {
            setIsHidden(true);
        }
    }, []);

    useEffect(() => {
        if (!isResizing) {
            localStorage.setItem('sidebarWidth', sidebarWidth.toString());
            localStorage.setItem('sidebarHidden', isHidden.toString());
        }
    }, [sidebarWidth, isHidden, isResizing]);

    useEffect(() => {
        if (sidebarWidth >= LABEL_MIN_WIDTH && isHidden) {
            setIsHidden(false);
        }
    }, [sidebarWidth, isHidden]);

    const startResizing = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        resizeStartX.current = e.clientX;
        resizeStartWidth.current = sidebarWidth;
        setIsResizing(true);
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'col-resize';
    }, [sidebarWidth]);

    const stopResizing = useCallback(() => {
        setIsResizing(false);
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
        if (resizeFrame.current) {
            cancelAnimationFrame(resizeFrame.current);
            resizeFrame.current = null;
        }
    }, []);

    const resize = useCallback(
        (e: MouseEvent) => {
            if (!isResizing) return;
            const delta = e.clientX - resizeStartX.current;
            const targetWidth = resizeStartWidth.current + delta;
            const clampedWidth = Math.min(MAX_WIDTH, Math.max(COLLAPSED_WIDTH, targetWidth));
            if (resizeFrame.current) return;
            resizeFrame.current = requestAnimationFrame(() => {
                resizeFrame.current = null;
                if (clampedWidth < LABEL_MIN_WIDTH) {
                    setIsHidden(true);
                    setSidebarWidth(COLLAPSED_WIDTH);
                } else {
                    setIsHidden(false);
                    setSidebarWidth(Math.max(LABEL_MIN_WIDTH, clampedWidth));
                }
            });
        },
        [isResizing]
    );

    useEffect(() => {
        window.addEventListener('mousemove', resize);
        window.addEventListener('mouseup', stopResizing);
        return () => {
            window.removeEventListener('mousemove', resize);
            window.removeEventListener('mouseup', stopResizing);
        };
    }, [resize, stopResizing]);

    const handleDisconnect = () => {
        localStorage.removeItem('fanet_node_id');
        localStorage.removeItem('fanet_role');
        router.push('/');
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex">
            <div
                ref={sidebarRef}
                className={`relative bg-slate-900/80 border-r border-slate-800 flex flex-col overflow-hidden ${
                    isResizing ? 'transition-none' : 'transition-all duration-200'
                } ${
                    isCollapsed ? 'items-center' : 'items-stretch'
                }`}
                style={{ width: sidebarWidth }}
            >
                <div className="flex items-center justify-between px-4 py-5">
                    <div className={`flex items-center gap-3 ${isCollapsed ? 'justify-center w-full' : ''}`}>
                        <div className="w-9 h-9 rounded-sm bg-blue-600/20 border border-blue-500/40 flex items-center justify-center">
                            <Radio size={18} className="text-blue-300" />
                        </div>
                        {!isCollapsed && (
                            <div>
                                <p className="text-xs uppercase tracking-wider text-slate-400 font-mono">Node</p>
                                <p className="text-sm font-semibold">{nodeId || 'UNASSIGNED'}</p>
                                <p className="text-[10px] uppercase text-slate-500">{role || 'UAV'}</p>
                            </div>
                        )}
                    </div>
                </div>

                <nav className="flex-1 px-2 space-y-2">
                    {menuItems.map((item) => {
                        const active = pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                href={item.path}
                                className={`flex items-center gap-3 px-3 py-2 rounded-sm text-sm uppercase tracking-wider font-mono transition-all ${
                                    active
                                        ? 'bg-blue-600/20 text-blue-200 border border-blue-500/40'
                                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                                } ${isCollapsed ? 'justify-center' : ''}`}
                                title={item.label}
                            >
                                <item.icon size={18} weight="duotone" />
                                {!isCollapsed && <span>{item.label}</span>}
                            </Link>
                        );
                    })}
                </nav>

                <button
                    onClick={handleDisconnect}
                    className={`m-3 px-3 py-2 rounded-sm text-xs uppercase tracking-wider font-mono flex items-center gap-2 border border-slate-700 hover:border-red-500/60 hover:text-red-300 transition ${
                        isCollapsed ? 'justify-center' : ''
                    }`}
                >
                    <SignOut size={16} />
                    {!isCollapsed && <span>Disconnect</span>}
                </button>

                <div
                    onMouseDown={startResizing}
                    className="absolute right-0 top-0 h-full w-1 cursor-col-resize bg-slate-800/60 hover:bg-blue-500/40"
                />
            </div>

            <main className="flex-1 min-h-screen">
                <div className="border-b border-slate-800 bg-slate-900/30 px-6 py-4 flex items-center justify-between">
                    <div>
                        <p className="text-xs uppercase tracking-wider text-slate-500 font-mono">GS-centric uplink control</p>
                        <h1 className="text-xl font-chivo uppercase tracking-wider">FANET Routing Console</h1>
                    </div>
                    <div className="text-right">
                        <p className="text-xs text-slate-500 font-mono">Status</p>
                        <p className="text-sm uppercase tracking-wider text-emerald-400">ONLINE</p>
                    </div>
                </div>
                <div className="p-6 space-y-6">{children}</div>
            </main>
        </div>
    );
}
