import React, { useEffect, useState } from 'react';
import { Modal, Button } from 'react-bootstrap';  // For Modal & Button
import { toast } from 'react-toastify';           // For toast notifications
import API from '../api';

const ManageBranch = () => {
    const [branch, setBranch] = useState(null);
    const [error, setError] = useState('');
    const [showThresholdModal, setShowThresholdModal] = useState(false);
    const [threshold, setThreshold] = useState(90);  // Default to 90%

    useEffect(() => {
        fetchBranch();
    }, []);

    const fetchBranch = async () => {
        try {
            const res = await API.post(`/branch/branches/`, { page: 1, limit: 1 }); // fetch 1 branch
            const data = res.data.branches;

            if (data.length > 0) {
                setBranch(data[0]);
                setThreshold(data[0].budget_alert_threshold || 90); // fallback to 90 if null
            }
        } catch (err) {
            console.error('Failed to fetch branch:', err);
            setError('Could not fetch branch details.');
        }
    };

    const handleThresholdUpdate = async () => {
        try {
            await API.patch(`/branch/set-threshold/${branch.branch_id}`, {
                threshold: parseFloat(threshold),
            });

            toast.success("Alert threshold updated!");
            setShowThresholdModal(false);
            fetchBranch();
        } catch (err) {
            console.error("Update failed:", err);
            toast.error("Failed to update threshold.");
        }
    };



    return (
        <div className="container mt-4">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2>Your Branch Information</h2>             {error && <div className="alert alert-danger">{error}</div>}

                <Button onClick={() => setShowThresholdModal(true)} style={{ backgroundColor: '#003153', border: 'none' }}>
                    Set Budget Alert Threshold
                </Button>
            </div>


            {branch ? (
                <div className="card p-4 shadow-sm">
                    <p><strong>Branch ID:</strong> {branch.branch_id}</p>
                    <p><strong>Name:</strong> {branch.branch_name}</p>
                    <p><strong>Location:</strong> {branch.blocation}</p>
                    <p><strong>Status:</strong> <span className={`badge ${branch.status === 'Active' ? 'bg-success' : 'bg-secondary'}`}>{branch.status}</span></p>
                    <p><strong>Handled By:</strong> {branch.manager_name ? `${branch.manager_name} (${branch.manager_email})` : 'N/A'}</p>
                    <p><strong>Budget Threshold:</strong> {branch.budget_alert_threshold}</p>
                </div>
            ) : (
                <p>No branch assigned or found.</p>
            )}

            <Modal show={showThresholdModal} onHide={() => setShowThresholdModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Set Alert Threshold</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <input
                        type="number"
                        className="form-control"
                        value={threshold}
                        min={1}
                        max={100}
                        onChange={(e) => setThreshold(e.target.value)}
                    />
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={handleThresholdUpdate}>Save</Button>
                </Modal.Footer>
            </Modal>
        </div>
    );
};

export default ManageBranch;
