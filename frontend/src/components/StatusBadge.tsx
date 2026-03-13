import React from 'react';

interface StatusBadgeProps {
    status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
    const normalized = status.toLowerCase();
    const className =
        normalized === 'active' || normalized === 'delivered'
            ? 'status-success'
            : normalized === 'buffered' || normalized === 'pending'
                ? 'status-pending'
                : 'status-failed';

    return (
        <span className={`inline-flex items-center px-2 py-1 rounded-sm border text-xs font-mono uppercase tracking-wider ${className}`}>
            {status}
        </span>
    );
}
