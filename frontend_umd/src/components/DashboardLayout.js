import React, { useEffect, useState } from 'react';
import { useNavigate, Link, NavLink } from 'react-router-dom';
import axios from 'axios';
import './DashboardLayout.css';
import API from '../api';
import { FaUserCircle } from 'react-icons/fa';

const DashboardLayout = ({ children, dashboardType }) => {
    const [user, setUser] = useState(null);
    const navigate = useNavigate();
    const [unreadCount, setUnreadCount] = useState(0);

    useEffect(() => {
        axios.get('http://localhost:5000/api/auth/me', {
            withCredentials: true
        })
            .then(res => setUser(res.data.user))
            .catch(() => navigate('/'));
    }, [navigate]);

    useEffect(() => {
        fetchUnreadAlerts();
    }, []);

    const handleLogout = () => {
        sessionStorage.clear();
        axios.post('http://localhost:5000/api/auth/logout', {}, { withCredentials: true })
            .then(() => {
                window.location.href = '/';
            });
    };

    const fetchUnreadAlerts = async () => {
        try {
            const res = await API.get('/alert/unread-count', { withCredentials: true });
            setUnreadCount(res.data.unread_count);
        } catch (err) {
            console.error("Failed to fetch unread alerts count");
        }
    };

    if (!user) return null;

    const roleId = user.role_id;

    return (
        <div className="dashboard-container">
            {/* Sidebar */}
            <div className="sidebar">
                <h4 className="fw-bold ps-3 sidebar-title">ExPilot</h4>
                <div className="ps-0 mb-2">
                    <div className="d-flex align-items-center ps-0 mb-1">
                        <FaUserCircle size={22} style={{ color: '#003153' }} className="me-2 mb-3" />
                        <p className="mb-0"><strong>{user.username}</strong><br /><small>{dashboardType}</small></p>
                    </div>
                </div>
                <ul className="nav flex-column">
                    {roleId === 1 && (
                        <>
                            <li className="nav-item">
                                <NavLink to="/dashboard/admin/your-account" className="nav-link">
                                    My Account
                                </NavLink>
                            </li>
                            <li className="nav-item">
                                <NavLink to={`/dashboard/${dashboardType.toLowerCase()}`}
                                    className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} >
                                    Overview
                                </NavLink>
                            </li>
                            <li className="nav-item">
                                <NavLink to="admin/users" className="nav-link">Manage Users</NavLink>
                            </li>
                            <li className="nav-item">
                                <NavLink to="admin/branches" className="nav-link">Manage Branches</NavLink>
                            </li>
                            <li className="nav-item">
                                <NavLink to="admin/budgetmanagement" className="nav-link">Budget Management</NavLink>
                            </li>
                            <li className="nav-item">
                                <NavLink to="admin/expensemanagement" className="nav-link">Expense Management</NavLink>
                            </li>
                            <li className="nav-item">
                                <NavLink to="admin/alerts" className="nav-link d-flex justify-content-between align-items-center">
                                    <span>Alerts</span>
                                    {unreadCount > 0 && (
                                        <span className="badge rounded-pill bg-danger ms-2">
                                            {unreadCount}
                                        </span>
                                    )}
                                </NavLink>
                            </li>
                        </>
                    )}

                    {roleId === 2 && (
                        <>
                            <li className="nav-item">
                                <NavLink to={`/dashboard/${dashboardType.toLowerCase()}`}
                                    className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                                    Overview
                                </NavLink>
                            </li>
                            <li className="nav-item">
                                <NavLink to="manage-branch" className="nav-link">Manage Branch</NavLink>
                            </li>
                            <li className="nav-item">
                                <Link to="managerbudgetmanagement" className="nav-link">Budget Management</Link>
                            </li>
                            <li className="nav-item">
                                <Link to="expensemanagement" className="nav-link">Expense Management</Link>
                            </li>
                            <li className="nav-item">
                                <Link to="alerts" className="nav-link d-flex justify-content-between align-items-center">
                                    <span>Alerts</span>
                                    {unreadCount > 0 && (
                                        <span className="badge rounded-pill bg-danger ms-2">
                                            {unreadCount}
                                        </span>
                                    )}
                                </Link>
                            </li>
                        </>
                    )}
                    {roleId === 3 && (
                        <>
                            <li className="nav-item">
                                <NavLink to="/dashboard/superadmin" className="nav-link">All Businesses</NavLink>
                            </li>
                        </>
                    )}
                </ul>
            </div>

            {/* Main Content Area */}
            <div className="main-content-wrapper">
                {/* Topbar */}
                <div className="topbar">
                    <h5 className="m-0">{dashboardType} Dashboard</h5>
                    <button className="logout-btn" onClick={handleLogout}>Logout</button>
                </div>
                {/* Content */}
                <div className="content p-4">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default DashboardLayout;
