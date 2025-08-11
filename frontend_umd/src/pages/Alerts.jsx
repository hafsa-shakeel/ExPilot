import React, { useEffect, useState } from 'react';
import API from '../api';
import { toast } from 'react-toastify';

const Alerts = () => {
    const [alerts, setAlerts] = useState([]);
    const [filter, setFilter] = useState('active');  // status filter
    const [severity, setSeverity] = useState('');    // severity filter
    const [unreadCount, setUnreadCount] = useState(0);

    useEffect(() => {
        markAlertsViewed();
    }, []);

    useEffect(() => {
        fetchAlerts();
    }, [filter, severity]);

    const markAlertsViewed = async () => {
        try {
            await API.patch('/alert/mark-viewed', {}, { withCredentials: true });
        } catch (err) {
            console.error('Failed to mark alerts as viewed:', err);
        }
    };

    const fetchAlerts = async () => {
        try {
            let endpoint = `/alert/alerts/filter?filter=${filter}`;
            if (severity) endpoint += `&severity=${severity}`;

            const res = await API.get(endpoint, { withCredentials: true });
            if (res.data.filtered_alerts) setAlerts(res.data.filtered_alerts);
            else setAlerts([]);
        } catch (err) {
            toast.error('Failed to fetch alerts');
        }
    };

    const handleResolve = async (id) => {
        try {
            await API.patch(`/alert/alerts/resolve/${id}`, {}, { withCredentials: true });
            fetchAlerts();
        } catch (err) {
            toast.error('Failed to resolve alert');
        }
    };

    const handleReopen = async (id) => {
        try {
            await API.patch(`/alert/alerts/reopen/${id}`, {}, { withCredentials: true });
            fetchAlerts();
        } catch (err) {
            toast.error('Failed to reopen alert');
        }
    };

    return (
        <div className="container mt-4">
            <h3>Alerts</h3>

            <div className="d-flex gap-2 mb-3">
                <select className="form-select w-auto" value={filter} onChange={(e) => setFilter(e.target.value)}>
                    <option value="active">Active</option>
                    <option value="resolved">Resolved</option>
                    <option value="all">All</option>
                </select>

                <select className="form-select w-auto" value={severity} onChange={(e) => setSeverity(e.target.value)}>
                    <option value="">All Severities</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                </select>
            </div>

            {alerts.length === 0 ? (
                <p>No alerts to display.</p>
            ) : (
                <table className="table table-bordered">
                    <thead>
                        <tr>
                            <th>Branch</th>
                            <th>Type</th>
                            <th>Severity</th>
                            <th>Message</th>
                            <th>Created At</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {alerts.map((alert) => (
                            <tr key={alert.id}>
                                <td>{alert.branch_name}</td>
                                <td>{alert.type}</td>
                                <td>{alert.severity}</td>
                                <td>{alert.message}</td>
                                <td>{new Date(alert.created_at).toLocaleString()}</td>
                                <td>
                                    {alert.status ? (
                                        alert.is_resolved ? 'Resolved' : 'Active'
                                    ) : (
                                        'Inactive'
                                    )}
                                </td>
                                <td>
                                    {alert.is_resolved ? (
                                        <button className="btn btn-sm btn-warning" onClick={() => handleReopen(alert.id)}>Reopen</button>
                                    ) : (
                                        <button className="btn btn-sm btn-success" onClick={() => handleResolve(alert.id)}>Resolve</button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};

export default Alerts;
