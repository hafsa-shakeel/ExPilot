import React, { useEffect, useState } from 'react';
import API from '../api';
import { toast } from 'react-toastify';
import { Modal, Button } from 'react-bootstrap';
import 'react-toastify/dist/ReactToastify.css';
import ImageComponent from '../components/ImageComponent';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { FaRegCalendarAlt } from 'react-icons/fa';


const ExpenseManagement = () => {
    const [expenses, setExpenses] = useState([]);
    const [filterBranchId, setFilterBranchId] = useState('');
    const [filterYear, setFilterYear] = useState('');
    const [filterMonth, setFilterMonth] = useState('');
    const [filterUtilityTypeId, setFilterUtilityTypeId] = useState('');
    const [options, setOptions] = useState({ branches: [], years: [], utility_types: [] });
    const [page, setPage] = useState(1);
    const [pageSize] = useState(10);
    const [totalPages, setTotalPages] = useState(1);
    const [refresh, setRefresh] = useState(false);
    const [mediaPreview, setMediaPreview] = useState(null);
    const [uploadForm, setUploadForm] = useState({
        branch_id: '',
        utility_type_id: '',
        year: '',
        month: '',
        units_used: '',
        amount: '',
        uploaded_by: '',
        media_file: null
    });
    const [showModal, setShowModal] = useState(false);
    const [utilityDetail, setUtilityDetail] = useState(null);
    const [showMediaModal, setShowMediaModal] = useState(false);
    const [mediaId, setMediaId] = useState(null);
    const [selectedMonthYear, setSelectedMonthYear] = useState(null);



    useEffect(() => {
        fetchFilters();
    }, []);

    useEffect(() => {
        fetchExpenses();
    }, [page, filterBranchId, filterYear, filterMonth, filterUtilityTypeId, refresh]);

    const fetchFilters = async () => {
        try {
            const res = await API.get(`/dashboard/expenses/filters`, { withCredentials: true });
            setOptions(res.data);
        } catch (err) {
            toast.error('Failed to load filters.');
        }
    };

    const fetchExpenses = async () => {
        try {
            const res = await API.post(`/dashboard/expenses/all`, {
                page,
                page_size: pageSize,
                branch_id: filterBranchId || undefined,
                year: filterYear || undefined,
                month: filterMonth || undefined,
                utility_type_id: filterUtilityTypeId || undefined
            }, { withCredentials: true });

            setExpenses(res.data.expenses);
            setTotalPages(res.data.total_pages || 1);
        } catch (err) {
            toast.error('Failed to fetch expenses.');
        }
    };

    const handleUploadChange = (e) => {
        const { name, value, files } = e.target;
        if (name === 'media_file') {
            setUploadForm({ ...uploadForm, media_file: files[0] });
        } else {
            setUploadForm({ ...uploadForm, [name]: value });
        }
    };

    const handleUploadSubmit = async (e) => {
        e.preventDefault();

        if (!selectedMonthYear) {
            toast.error("Please select Month and Year");
            return;
        }

        const formData = new FormData();
        for (const key in uploadForm) {
            if (uploadForm[key]) {
                formData.append(key, uploadForm[key]);
            }
        }

        const month = selectedMonthYear.getMonth() + 1;
        const year = selectedMonthYear.getFullYear();
        formData.append("month", month);
        formData.append("year", year);

        try {
            await API.post(`/utility/utility-bills/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                withCredentials: true
            });
            toast.success('Utility bill uploaded.');
            setUploadForm({
                branch_id: '', utility_type_id: '', year: '', month: '',
                units_used: '', amount: '', uploaded_by: '', media_file: null
            });
            setSelectedMonthYear(null); // clear calendar
            document.querySelector("input[name='media_file']").value = null;
            setRefresh(prev => !prev);
        } catch (err) {
            toast.error('Upload failed.');
        }
    };

    const handleDelete = async (id) => {
        try {
            await API.delete(`/utility/utility-bills/delete/${id}`, { withCredentials: true });
            toast.success('Utility bill deleted.');
            setRefresh(prev => !prev);
        } catch (err) {
            toast.error('Delete failed.');
        }
    };

    const handleGetDetails = async (id) => {
        try {
            const res = await API.get(`/utility/utility-bills/${id}`, { withCredentials: true });
            setUtilityDetail(res.data);
            setShowModal(true);
        } catch (err) {
            toast.error('Failed to fetch utility detail');
        }
    };

    return (
        <div className="container mt-4">
            <h3 className="mb-3">Expense Management</h3>

            <div className="card p-4 mb-4">
                <h5>Upload Utility Bill</h5>
                <form onSubmit={handleUploadSubmit} className="d-flex flex-wrap gap-2 align-items-center">

                    {/* Branch dropdown */}
                    <select
                        name="branch_id"
                        value={uploadForm.branch_id}
                        onChange={handleUploadChange}
                        required
                        className="form-select"
                    >
                        <option value="">Select Branch</option>
                        {options.branches.map(branch => (
                            <option key={branch.branch_id} value={branch.branch_id}>{branch.branch_name}</option>
                        ))}
                    </select>

                    <select name="utility_type_id" value={uploadForm.utility_type_id} onChange={handleUploadChange} required className="form-select">
                        <option value="">Select Utility</option>
                        {options.utility_types.map(u => (
                            <option key={u.id} value={u.id}>{u.utility_name}</option>
                        ))}
                    </select>
                    <div>
                        <div className="position-relative w-auto">
                            <label className="form-label"></label>
                            <DatePicker
                                selected={selectedMonthYear}
                                onChange={(date) => setSelectedMonthYear(date)}
                                dateFormat="MM/yyyy"
                                showMonthYearPicker
                                showFullMonthYearPicker
                                className="form-control ps-5"
                                placeholderText="Select Month & Year"
                                calendarClassName="shadow"
                                popperPlacement="bottom-start"
                            />
                            <FaRegCalendarAlt className="position-absolute top-50 start-0 translate-middle-y ms-3 text-muted" />
                        </div>

                    </div>


                    <input className="form-control" name="units_used" placeholder="Units Used" value={uploadForm.units_used} onChange={handleUploadChange} />

                    <input className="form-control" name="amount" placeholder="Amount" value={uploadForm.amount} onChange={handleUploadChange} required />

                    <input className="form-control" name="media_file" type="file" accept=".pdf,.csv,.jpg,.jpeg,.png" onChange={handleUploadChange} required />

                    <button
                        type="submit"
                        className="btn"
                        style={{ backgroundColor: '#003153', color: 'white', border: 'none' }}
                    >
                        Upload
                    </button>
                </form>
            </div>

            {/* Filter Controls */}
            <div className="d-flex gap-2 mb-3 align-items-end">
                <div>
                    <label>Branch</label>
                    <select className="form-control" value={filterBranchId} onChange={(e) => setFilterBranchId(e.target.value)}>
                        <option value="">All Branches</option>
                        {options.branches.map((b) => (
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
                        {["January", "February", "March", "April", "May", "June", "July", "August",
                            "September", "October", "November", "December"].map((m, idx) => (
                                <option key={idx + 1} value={idx + 1}>{m}</option>
                            ))}
                    </select>
                </div>

                <div>
                    <label>Utility</label>
                    <select className="form-control" value={filterUtilityTypeId} onChange={(e) => setFilterUtilityTypeId(e.target.value)}>
                        <option value="">All Utilities</option>
                        {options.utility_types.map(u => (
                            <option key={u.id} value={u.id}>{u.utility_name}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Expense Table */}
            <table className="table table-bordered">
                <thead>
                    <tr>
                        <th>Branch</th>
                        <th>Utility</th>
                        <th>Category</th>
                        <th>Year</th>
                        <th>Month</th>
                        <th>Amount</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {expenses.map(e => (
                        <tr key={e.expense_id}>
                            <td>{e.branch_name}</td>
                            <td>{e.utility_name}</td>
                            <td>{e.category}</td>
                            <td>{e.year}</td>
                            <td>{e.month}</td>
                            <td>{e.amount}</td>
                            <td>

                                <button className="btn btn-sm me-2" onClick={() => handleGetDetails(e.expense_id)} style={{ backgroundColor: '#003153', color: 'white' }}>Detail</button>
                                <button className="btn btn-sm btn-danger me-2" onClick={() => handleDelete(e.expense_id)}>Remove</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {/* Pagination */}
            <div className="d-flex justify-content-between">
                <button className="btn btn-outline-primary" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button>
                <span>Page {page} of {totalPages}</span>
                <button className="btn btn-outline-primary" disabled={page === totalPages} onClick={() => setPage(page + 1)}>Next</button>
            </div>

            {/* Detail Modal */}
            <Modal show={showModal} onHide={() => setShowModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Utility Detail</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {utilityDetail ? (
                        <div>
                            <p><strong>Branch:</strong> {utilityDetail.branch_name}</p>
                            <p><strong>Utility:</strong> {utilityDetail.utility_name}</p>
                            <p><strong>Category:</strong> {utilityDetail.category}</p>
                            <p><strong>Year:</strong> {utilityDetail.year}</p>
                            <p><strong>Month:</strong> {utilityDetail.month}</p>
                            <p><strong>Units Used:</strong> {utilityDetail.units_used}</p>
                            <p><strong>Amount:</strong> {utilityDetail.amount}</p>
                            <p><strong>Uploaded At:</strong> {utilityDetail.uploaded_at}</p>
                            <p><strong>Uploaded By:</strong> {utilityDetail.uploaded_by}</p>
                        </div>
                    ) : <p>Loading...</p>}
                </Modal.Body>
                <Modal.Footer>
                </Modal.Footer>
            </Modal>



        </div>
    );
};

export default ExpenseManagement;
