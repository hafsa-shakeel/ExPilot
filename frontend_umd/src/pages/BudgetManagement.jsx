import React, { useEffect, useState } from 'react';
import API from '../api';
import { toast } from 'react-toastify';
import { Modal } from 'react-bootstrap';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { FaRegCalendarAlt } from 'react-icons/fa';

const BudgetManagement = () => {
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
    const [limit] = useState(10);
    const [totalPages, setTotalPages] = useState(1);
    const [filterYear, setFilterYear] = useState('');
    const [filterMonth, setFilterMonth] = useState('');
    const [filterBranchId, setFilterBranchId] = useState('');
    const [selectedBudget, setSelectedBudget] = useState(null);
    const [detailsModalOpen, setDetailsModalOpen] = useState(false);
    const [recommendedBudget, setRecommendedBudget] = useState(null);
    const [selectedMonthYear, setSelectedMonthYear] = useState(null);


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

    useEffect(() => {
        fetchRecommendation(form.branch_id, form.year, form.month);
    }, [form.branch_id, form.year, form.month]);

    const handleUploadChange = (e) => {
        const { name, value } = e.target;
        setForm((prevForm) => ({
            ...prevForm,
            [name]: value
        }));
    };

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

    const handleSubmit = async () => {
        try {
            if (selectedMonthYear) {
                form.month = selectedMonthYear.getMonth() + 1;
                form.year = selectedMonthYear.getFullYear();
            }

            if (budget) {
                await API.patch(`/budget/update/${budget.id}`, form, { withCredentials: true });
                toast.success("Budget updated");
            } else {
                await API.post(`/budget/add`, form, { withCredentials: true });
                toast.success("Budget added");
            }

            setForm({ branch_id: '', month: '', year: '', total_budget: '' });
            setSelectedMonthYear(null);
            setbudget(null);
            fetchBudgets({ pageNumber: 1 });
        } catch (err) {
            if (err.response?.status === 403 && err.response?.data?.error?.includes("48-hour")) {
                const confirmReallocate = window.confirm("48-hour window expired. Do you want to reallocate budget?");
                if (confirmReallocate) {
                    try {
                        await API.patch(`/budget/update/${budget.id}?reallocate=true`, form, { withCredentials: true });
                        toast.success("Budget reallocated successfully.");
                        fetchBudgets({ pageNumber: 1 });
                        setForm({ branch_id: '', month: '', year: '', total_budget: '' });
                        setbudget(null);
                    } catch (e) {
                        toast.error(e.response?.data?.error || "Reallocation failed.");
                    }
                }
            } else {
                toast.error(err.response?.data?.error || "Operation failed");
            }
        }
    };

    const handleReallocate = (b) => {
        if (!b.canReallocate) {
            if (parseFloat(b.total_budget) > 0) {
                toast.info("Budget not entirely consumed.");
            } else {
                toast.info("48hrs window has not yet passed.");
            }
            return;
        }
        startEdit(b);
    };

    const startEdit = (budget) => {
        setbudget(budget);
        setForm({
            branch_id: budget.branch_id,
            month: budget.month,
            year: budget.year,
            total_budget: budget.total_budget
        });
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

    const fetchRecommendation = async (branchId, year, month) => {
        if (!branchId || !year || !month) return;
        try {
            const res = await API.get(`/dashboard/reports/budget-recommendation/${branchId}?year=${year}&month=${month}`, {
                withCredentials: true
            });
            if (res.data.recommended_budget) {
                setRecommendedBudget(res.data.recommended_budget);
            }
            else if (res.data.message) {
                setRecommendedBudget(null);
                toast.info(res.data.message);           // <── toast here
            } else {
                setRecommendedBudget(null);

            }
        } catch (error) {
            console.error("Failed to fetch recommendation", error);
            setRecommendedBudget(null);
        }
    };

    return (
        <div className="container mt-4">
            <h3 className="mb-3">Budget Management</h3>
            <div className="card p-4 mb-4">
                <h5>{budget ? "Edit Budget" : "Add Budget"}</h5>
                <select className="form-control mb-0" name="branch_id" value={form.branch_id} onChange={handleUploadChange}>
                    <option value="">Select Branch</option>
                    {branches.map((b) => (
                        <option key={b.branch_id} value={b.branch_id}>{b.branch_name}</option>
                    ))}
                </select>

                <div>
                    <div style={{ marginTop: '0px' }} className="d-flex flex-column position-relative">
                        <label className="form-label"></label>
                        <DatePicker
                            selected={selectedMonthYear}
                            onChange={(date) => setSelectedMonthYear(date)}
                            dateFormat="MM/yyyy"
                            showMonthYearPicker
                            showFullMonthYearPicker
                            className="form-control ps-5 mb-2"
                            placeholderText="Select Month & Year"
                            calendarClassName="shadow"
                            popperPlacement="bottom-start"
                        />
                        <FaRegCalendarAlt className="position-absolute top-50 start-0 translate-middle-y ms-3 text-muted" />
                    </div>

                </div>


                <div style={{ position: 'relative', width: '100%' }}>
                    <input
                        className="form-control"
                        name="total_budget"
                        placeholder="Total Budget"
                        value={form.total_budget}
                        onChange={handleUploadChange}
                        required
                    />
                    {recommendedBudget && (
                        <small style={{
                            position: 'absolute',
                            top: '100%',
                            right: 0,
                            color: 'green',
                            fontWeight: 'bold',
                            fontSize: '0.85rem'
                        }}>
                            💡 Recommended: Rs. {recommendedBudget}
                        </small>
                    )}
                </div>

                <div className="d-flex gap-2 mt-2">
                    <button className="btn" style={{ backgroundColor: '#003153', color: 'white' }} onClick={handleSubmit}>
                        {budget ? "Update" : "Add"}
                    </button>
                    {budget && (
                        <button className="btn btn-secondary" onClick={() => {
                            setbudget(null);
                            setForm({ branch_id: '', month: '', year: '', total_budget: '' });
                        }}>Cancel</button>
                    )}
                </div>
            </div>

            <div className="d-flex gap-2 mb-3 align-items-end">
                <div>
                    <label>Branch</label>
                    <select className="form-control" value={filterBranchId} onChange={(e) => setFilterBranchId(e.target.value)}>
                        <option value="">All Branches</option>
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
                                    <button className="btn btn-sm me-2" style={{ backgroundColor: '#003153', color: 'white' }} onClick={() => startEdit(b)}>Edit</button>
                                    <button className="btn btn-sm btn-secondary me-2" onClick={() => fetchBudgetDetails(b.id)}>View</button>
                                    <button className="btn btn-sm btn-warning" onClick={() => handleReallocate(b)}>Reallocate</button>
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>

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
            </Modal>

            <div className="d-flex justify-content-between">
                <button className="btn btn-outline-primary" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button>
                <span>Page {page} of {totalPages}</span>
                <button className="btn btn-outline-primary" disabled={page === totalPages} onClick={() => setPage(page + 1)}>Next</button>
            </div>
        </div>
    );
};

export default BudgetManagement;
