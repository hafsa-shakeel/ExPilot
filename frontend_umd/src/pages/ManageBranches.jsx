import React, { useEffect, useState } from 'react';
import API from '../api';
import { Modal, Button } from 'react-bootstrap';  // For Modal & Button
import { toast } from 'react-toastify';           // For toast notifications

const ManageBranches = () => {
    const [branches, setBranches] = useState([]);
    const [selectedBranchId, setSelectedBranchId] = useState(null);
    const [managers, setManagers] = useState([]);
    const [formData, setFormData] = useState({ branch_name: '', blocation: '', handled_by: '' });
    const [editingBranch, setEditingBranch] = useState(null);
    const [error, setError] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const limit = 2;
    const [showThresholdModal, setShowThresholdModal] = useState(false);
    const [threshold, setThreshold] = useState(90);  // Default to 90%

    const fetchBranches = async () => {
        try {
            const res = await API.post(`/branch/branches/`, { page, limit });
            setBranches(res.data.branches);
            setTotalPages(Math.ceil(res.data.total / limit));
        } catch (err) {
            console.error('Fetch branches failed:', err);
        }
    };

    const fetchManagers = async () => {
        try {
            const res = await API.get('/branch/branch-managers/available');
            setManagers(res.data.available_branch_managers || []);
            console.log("Refreshed manager list:", res.data.available_branch_managers); //
        } catch (err) {
            console.error('Fetch managers failed:', err);
        }
    };

    useEffect(() => {
        fetchBranches();
        fetchManagers();
    }, [page]);

    const handleChange = e => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleAddOrUpdate = async () => {
        try {
            if (editingBranch) {
                await API.patch(`/branch/branches/update/${editingBranch.branch_id}`, formData);
            } else {
                await API.post(`/branch/branch-add`, formData);
            }

            //refresh manager list and branches after change
            fetchBranches();
            fetchManagers();

            // Reset form and edit state
            setFormData({ branch_name: '', blocation: '', handled_by: '' });
            setEditingBranch(null);
        } catch (err) {
            console.error('Add/Update branch failed:', err);
        }
    };

    const handleEdit = (branch) => {
        setEditingBranch(branch);
        setFormData({
            branch_name: branch.branch_name,
            blocation: branch.blocation,
            handled_by: ''  // Force user to re-select to ensure valid manager
        });
    };

    const handleDelete = async (id) => {
        try {
            await API.delete(`/branch/branches/${id}`);
            fetchBranches();
            fetchManagers(); //important for manager availability
        } catch (err) {
            console.error('Deactivate branch failed:', err);
        }
    };

    const handleReactivate = async (id) => {
        try {
            await API.patch(`/branch/reactivate/${id}`);
            fetchBranches();
            fetchManagers(); //in case manager list needs update
        } catch (err) {
            console.error('Reactivate branch failed:', err);
        }
    };

    const handleThresholdUpdate = async () => {
        try {
            await API.patch(`/branch/set-threshold/${selectedBranchId}`, {
                threshold: parseFloat(threshold),
            });
            toast.success("Alert threshold updated!");
            setShowThresholdModal(false);
            setSelectedBranchId(null);
            fetchBranches();
        } catch (err) {
            console.error("Update failed:", err);
            toast.error("Failed to update threshold.");
        }
    };



    return (
        <div className="container mt-4">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2>{editingBranch ? 'Edit Branch' : 'Add Branch'}</h2>            {error && <div className="alert alert-danger">{error}</div>}
            </div>
            <div className="card p-4 mb-4">
                <input
                    type="text"
                    className="form-control mb-2"
                    placeholder="Branch Name"
                    name="branch_name"
                    value={formData.branch_name}
                    onChange={handleChange}
                />
                <input
                    type="text"
                    className="form-control mb-2"
                    placeholder="Location"
                    name="blocation"
                    value={formData.blocation}
                    onChange={handleChange}
                />
                <select
                    className="form-control mb-2"
                    name="handled_by"
                    value={formData.handled_by}
                    onChange={handleChange}
                >
                    <option value="">Select Manager</option>
                    {managers.map(mgr => (
                        <option key={mgr.user_id} value={mgr.user_id}>
                            {mgr.username} ({mgr.email})
                        </option>
                    ))}
                </select>

                <div className="d-flex gap-2"><button className="btn"
                    style={{ backgroundColor: '#003153', color: 'white', width: '80px', fontSize: '14px' }}
                    onClick={handleAddOrUpdate}> {editingBranch ? 'Update' : 'Add'}
                </button>

                    {editingBranch && (
                        <button className="btn btn-secondary" style={{ width: '80px', fontSize: '14px' }}
                            onClick={() => {
                                setEditingBranch(null);
                                setFormData({ branch_name: '', blocation: '', handled_by: '' });
                                fetchManagers();
                            }}>Cancel
                        </button>)}
                </div>



            </div>

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

            <table className="table table-bordered">
                <thead>
                    <tr>
                        <th>Branch ID</th>
                        <th>Name</th>
                        <th>Location</th>
                        <th>Handled By</th>
                        <th>Budget Threshold</th>
                        <th>Current Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {branches.map(branch => (
                        <tr key={branch.branch_id}>
                            <td>{branch.branch_id}</td>
                            <td>{branch.branch_name}</td>
                            <td>{branch.blocation}</td>
                            <td>
                                {branch.manager_name
                                    ? `${branch.manager_name} (${branch.manager_email})`
                                    : 'N/A'}
                            </td>
                            <td>{branch.budget_alert_threshold}</td>
                            <td>
                                <span className={`badge ${branch.status === 'Active' ? 'bg-success' : 'bg-secondary'}`}>
                                    {branch.status}
                                </span>
                            </td>
                            <td className="d-flex flex-column gap-1">
                                {branch.status === 'Active' ? (
                                    <>
                                        <button
                                            className="btn btn-sm"
                                            style={{ backgroundColor: '#003153', color: 'white' }}
                                            onClick={() => handleEdit(branch)}
                                        >
                                            Edit
                                        </button>

                                        <button
                                            className="btn btn-danger btn-sm"
                                            onClick={() => handleDelete(branch.branch_id)}
                                        >
                                            Deactivate
                                        </button>

                                        <button
                                            className="btn btn-sm"
                                            onClick={() => {
                                                setSelectedBranchId(branch.branch_id);
                                                setThreshold(branch.budget_alert_threshold || 90);
                                                setShowThresholdModal(true);
                                            }} style={{ backgroundColor: '#003153', color: 'white' }}

                                        >
                                            Set Threshold
                                        </button>
                                    </>
                                ) : (
                                    <button
                                        className="btn btn-warning btn-sm"
                                        onClick={() => handleReactivate(branch.branch_id)}
                                    >
                                        Reactivate
                                    </button>
                                )}
                            </td>

                        </tr>
                    ))}
                </tbody>
            </table>

            <div className="d-flex justify-content-between align-items-center mt-3">
                <button
                    className="btn btn-outline-primary btn-sm"
                    disabled={page === 1}
                    onClick={() => setPage(prev => prev - 1)}
                >
                    Previous
                </button>

                <span className="mx-2 small">Page {page} of {totalPages}</span>

                <button
                    className="btn btn-outline-primary btn-sm"
                    disabled={page === totalPages}
                    onClick={() => setPage(prev => prev + 1)}
                >
                    Next
                </button>
            </div>

        </div>
    );
};

export default ManageBranches;
