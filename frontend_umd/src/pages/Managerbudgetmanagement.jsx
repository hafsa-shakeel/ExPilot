import React, { useEffect, useState } from 'react';
import API from '../api';
import { toast } from 'react-toastify';
import { Modal, Button } from 'react-bootstrap';


const Managerbudgetmanagement = () => {
    const [budgets, setBudgets] = useState([]);
    const [branches, setBranches] = useState([]);
    const [form, setForm] = useState({
        branch_id: '',
        month: '',
        year: '',
        total_budget: ''
    });
    const [budget, setbudget] = useState(null);
    const [page, setPage] = useState(1);
    const [limit] = useState(5);
    const [totalPages, setTotalPages] = useState(1);
    const [filterYear, setFilterYear] = useState('');
    const [filterMonth, setFilterMonth] = useState('');
    const [filterBranchId, setFilterBranchId] = useState('');
    const [selectedBudget, setSelectedBudget] = useState(null);
    const [detailsModalOpen, setDetailsModalOpen] = useState(false);

    useEffect(() => {
        fetchBranches();
    }, []);

    useEffect(() => {
        setPage(1);
        fetchBudgets({ pageNumber: 1 });
    }, [filterBranchId, filterYear, filterMonth]);

    useEffect(() => {
        fetchBudgets({ pageNumber: page });
    }, [page]);

    const fetchBranches = async () => {
        try {
            const res = await API.post(`/branch/branches/`, {}, { withCredentials: true });
            setBranches(res.data.branches);
        } catch (err) {
            toast.error("Failed to load branches");
        }
    };

    const fetchBudgets = async ({ pageNumber = 1 }) => {
        try {
            const res = await API.post(`/budget/view`, {
                page: pageNumber,
                limit,
                year: filterYear || undefined,
                month: filterMonth || undefined,
                branch_id: filterBranchId || undefined
            }, { withCredentials: true });

            const enhancedBudgets = res.data.budgets.map(b => {
                const createdAt = new Date(b.created_at);
                const isAfter48Hours = new Date() > new Date(createdAt.getTime() + 48 * 60 * 60 * 1000);
                const isConsumed = parseFloat(b.total_budget) === 0;
                return {
                    ...b,
                    canReallocate: isAfter48Hours && isConsumed
                };
            });

            setBudgets(enhancedBudgets);
            setTotalPages(Math.ceil((res.data.total_records || 1) / limit));
            setPage(pageNumber);
        } catch (error) {
            toast.error("Failed to load budgets");
        }
    };


    const fetchBudgetDetails = async (id) => {
        try {
            const res = await API.get(`/budget/budgets/${id}`, { withCredentials: true });
            setSelectedBudget(res.data.budget);
            setDetailsModalOpen(true);
        } catch (err) {
            toast.error("Failed to fetch budget details.");
        }
    };

    return (
        <div className="container mt-4">
            <h3 className="mb-3">Budget Management</h3>

            <div className="page-container" style={{ display: 'flex', flexDirection: 'column', minHeight: '80vh' }}>
                <div className="table-container" style={{ flexGrow: 1 }}>

                    <div className="d-flex gap-2 mb-3 align-items-end">
                        <div>
                            <label>Branch</label>
                            <select className="form-control" value={filterBranchId} onChange={(e) => setFilterBranchId(e.target.value)}>
                                <option value="">Select Branch</option>
                                {branches.map((b) => (
                                    <option key={b.branch_id} value={b.branch_id}>{b.branch_name}</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label>Year</label>
                            <select className="form-control" value={filterYear} onChange={(e) => setFilterYear(e.target.value)}>
                                <option value="">All Years</option>
                                {[2024, 2025, 2026, 2027].map((y) => (
                                    <option key={y} value={y}>{y}</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label>Month</label>
                            <select className="form-control" value={filterMonth} onChange={(e) => setFilterMonth(e.target.value)}>
                                <option value="">All Months</option>
                                {["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].map((m, idx) => (
                                    <option key={idx + 1} value={idx + 1}>{m}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <table className="table table-bordered">
                        <thead>
                            <tr>
                                <th>Branch</th>
                                <th>Month</th>
                                <th>Year</th>
                                <th>Total Budget</th>
                                <th>Spent</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {budgets.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="text-center">No budgets found.</td>
                                </tr>
                            ) : (
                                budgets.map(b => (
                                    <tr key={b.id}>
                                        <td>{b.branch}</td>
                                        <td>{b.month}</td>
                                        <td>{b.year}</td>
                                        <td>{b.total_budget}</td>
                                        <td>{b.total_spent}</td>
                                        <td>

                                            <button
                                                className="btn btn-sm btn-secondary me-2"
                                                onClick={() => fetchBudgetDetails(b.id)}
                                            >View</button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                <Modal show={detailsModalOpen} onHide={() => setDetailsModalOpen(false)}>
                    <Modal.Header closeButton>
                        <Modal.Title>Budget Details</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        {selectedBudget ? (
                            <div>
                                <p><strong>Branch:</strong> {selectedBudget.branch}</p>
                                <p><strong>Month:</strong> {selectedBudget.month}</p>
                                <p><strong>Year:</strong> {selectedBudget.year}</p>
                                <p><strong>Total Budget:</strong> {selectedBudget.total_budget}</p>
                                <p><strong>Total Spent:</strong> {selectedBudget.total_spent}</p>
                                <p><strong>Created At:</strong> {selectedBudget.created_at}</p>
                            </div>
                        ) : (
                            <p>Loading...</p>
                        )}
                    </Modal.Body>
                    <Modal.Footer>
                    </Modal.Footer>
                </Modal>


                <div className="d-flex justify-content-between">
                    <button className="btn btn-outline-primary" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button>
                    <span>Page {page} of {totalPages}</span>
                    <button className="btn btn-outline-primary" disabled={page === totalPages} onClick={() => setPage(page + 1)}>Next</button>
                </div>
            </div>


        </div>
    );
};

export default Managerbudgetmanagement;
