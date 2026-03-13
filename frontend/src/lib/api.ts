const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
    private async request(endpoint: string, options: RequestInit = {}) {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string>),
        };

        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers,
            cache: 'no-store',
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || error.message || 'Request failed');
        }

        return response.json();
    }

    async registerNode(id: string, role: 'GS' | 'UAV') {
        return this.request('/nodes', {
            method: 'POST',
            body: JSON.stringify({ id, role }),
        });
    }

    async listNodes() {
        return this.request('/nodes');
    }

    async updateNeighbors(nodeId: string, neighbors: any[]) {
        return this.request(`/neighbors/${nodeId}`, {
            method: 'POST',
            body: JSON.stringify({ neighbors }),
        });
    }

    async listNeighbors(nodeId: string) {
        return this.request(`/neighbors/${nodeId}`);
    }

    async emitFlood(gsId: string, floodTtl?: number) {
        return this.request('/flood/emit', {
            method: 'POST',
            body: JSON.stringify({ gs_id: gsId, flood_ttl: floodTtl }),
        });
    }

    async sendData(payload: {
        source_uav_id: string;
        gs_id?: string;
        payload_type: string;
        payload_size: number;
        priority_level: 'EMERGENCY' | 'HIGH' | 'STANDARD';
        payload?: string;
        ttl?: number;
    }) {
        return this.request('/data/send', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async sendControl(payload: {
        control_type: 'ROUTE_ERROR' | 'BUFFER_STATUS' | 'SATELLITE_ACTIVATION_NOTICE';
        source_id: string;
        destination_id: string;
        detail?: string;
        data?: Record<string, any>;
    }) {
        return this.request('/control/send', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async getRoutes() {
        return this.request('/routes');
    }

    async getBuffer() {
        return this.request('/buffer');
    }

    async getSatelliteStates() {
        return this.request('/satellite');
    }

    async getMetricsSummary() {
        return this.request('/metrics/summary');
    }

    async getMetricsCounters() {
        return this.request('/metrics/counters');
    }

    async getEvents() {
        return this.request('/events');
    }

    async getHealth() {
        return this.request('/health');
    }

    async getConfig() {
        return this.request('/config');
    }

    async getAssumptions() {
        return this.request('/assumptions');
    }

    async updateConfig(data: Record<string, any>) {
        return this.request('/config', {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async tick(gsId?: string) {
        return this.request('/tick', {
            method: 'POST',
            body: JSON.stringify({ gs_id: gsId }),
        });
    }

    async seedSimulation(payload: {
        gs_id?: string;
        uav_count?: number;
        uav_prefix?: string;
        neighbor_degree?: number;
        topology?: string;
        reset?: boolean;
        auto_flood?: boolean;
        auto_data?: boolean;
        sample_packets?: number;
    }) {
        return this.request('/simulate/seed', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async simulateRun(payload: Record<string, any>) {
        return this.request('/simulate/run', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async simulateStop() {
        return this.request('/simulate/stop', { method: 'POST' });
    }

    async simulateStatus() {
        return this.request('/simulate/status');
    }
}

export const api = new ApiClient();
