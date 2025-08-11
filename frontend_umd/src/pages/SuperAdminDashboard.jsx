import React, { useEffect, useState } from 'react';
import API from '../api';
import { toast } from 'react-toastify';
import DashboardLayout from '../components/DashboardLayout';

const SuperAdminDashboard = () => {
    const [businesses, setBusinesses] = useState([]);
    const [selectedBusiness, setSelectedBusiness] = useState(null);
    const [message, setMessage] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 5;

    useEffect(() => {
        fetchBusinesses();
    }, []);

    const fetchBusinesses = async () => {
        try {
            const response = await API.get('/auth/businesses');
            setBusinesses(response.data.businesses);
        } catch (err) {
            console.error('Failed to fetch businesses', err);
        }
    };

    const fetchBusinessDetail = async (business_id) => {
        try {
            const response = await API.get(`/auth/businesses/${business_id}`);
            setSelectedBusiness(response.data);
            setMessage('');
        } catch (err) {
            setMessage("Error fetching business details");
        }
    };

    const approveBusiness = async (business_id) => {
        try {
            await API.post(`/auth/approve-business/${business_id}`);
            setMessage('Business approved successfully.');
            toast.success("Admin of the business is notified!");
            fetchBusinesses();
            setSelectedBusiness(null);
        } catch (err) {
            setMessage('Error approving business.');
        }
    };

    const rejectBusiness = async (business_id) => {
        try {
            await API.post(`/auth/reject-business/${business_id}`);
            setMessage('Business rejected successfully.');
            toast.success("Admin of the business is notified!");
            fetchBusinesses();
            setSelectedBusiness(null);
        } catch (err) {
            setMessage('Error rejecting business.');
        }
    };

    const filteredBusinesses = businesses.filter(biz =>
        statusFilter === 'all' ? true : biz.req_status === statusFilter
    );

    const paginatedBusinesses = filteredBusinesses.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    const totalPages = Math.ceil(filteredBusinesses.length / itemsPerPage);

    const getStatusBadge = (status) => {
        const colors = {
            approved: 'success',
            pending: 'warning',
            rejected: 'danger'
        };
        return (
            <span className={`badge bg-${colors[status] || 'secondary'}`}>
                {status}
            </span>
        );
    };

    return (
        <DashboardLayout dashboardType="SuperAdmin">
            {message && <div className="alert alert-info">{message}</div>}

            <h5 className="mb-3">All Businesses</h5>

            {/* Filters */}
            <div className="d-flex align-items-center gap-2 mb-3">
                <select
                    className="form-select w-auto"
                    value={statusFilter}
                    onChange={(e) => {
                        setStatusFilter(e.target.value);
                        setCurrentPage(1);
                    }}
                >
                    <option value="all">All</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                </select>
                {statusFilter !== 'all' && (
                    <button className="btn btn-secondary btn-sm" onClick={() => {
                        setStatusFilter('all');
                        setCurrentPage(1);
                    }}>
                        Clear Filters
                    </button>
                )}
            </div>

            <ul className="list-group mb-4">
                {paginatedBusinesses.map((biz) => (
                    <li key={biz.business_id} className="list-group-item d-flex justify-content-between align-items-center">
                        <span>
                            {biz.business_name} {getStatusBadge(biz.req_status)}
                        </span>
                        <button className="btn btn-sm" onClick={() => fetchBusinessDetail(biz.business_id)} style={{ backgroundColor: '#003153', color: 'white' }}>View</button>
                    </li>
                ))}
            </ul>

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="d-flex justify-content-center mb-4">
                    <nav>
                        <ul className="pagination">
                            {[...Array(totalPages)].map((_, i) => (
                                <li key={i} className={`page-item ${currentPage === i + 1 ? 'active' : ''}`}>
                                    <button className="page-link" onClick={() => setCurrentPage(i + 1)}>
                                        {i + 1}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </nav>
                </div>
            )}

            {/* Business Details */}
            {selectedBusiness && (
                <div className="card p-3 position-relative">
                    <button
                        className="btn-close position-absolute top-0 end-0 m-3"
                        onClick={() => setSelectedBusiness(null)}
                        aria-label="Close"
                    ></button>
                    <h5>Business Details</h5>
                    <p><strong>Name:</strong> {selectedBusiness.business.business_name}</p>
                    <p><strong>Industry:</strong> {selectedBusiness.business.industry}</p>
                    <p><strong>Email:</strong> {selectedBusiness.business.email}</p>
                    <p><strong>Contact Person:</strong> {selectedBusiness.business.contact_person}</p>
                    <p><strong>Status:</strong> {selectedBusiness.business.status}</p>
                    <p><strong>Request Status:</strong> {getStatusBadge(selectedBusiness.business.req_status)}</p>
                    <p><strong>Total Branches:</strong> {selectedBusiness.total_branches}</p>
                    <p><strong>Total Users:</strong> {selectedBusiness.total_users}</p>

                    {selectedBusiness.business.req_status === 'pending' && (
                        <div className="mt-3">
                            <button className="btn btn-success me-2" onClick={() => approveBusiness(selectedBusiness.business.business_id)}>Approve</button>
                            <button className="btn btn-danger" onClick={() => rejectBusiness(selectedBusiness.business.business_id)}>Reject</button>
                        </div>
                    )}
                </div>
            )}
        </DashboardLayout>
    );
};

export default SuperAdminDashboard;
