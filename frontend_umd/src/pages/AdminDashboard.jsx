import React from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { Outlet } from 'react-router-dom';

const AdminDashboard = () => {
    return (
        <DashboardLayout dashboardType="Admin">
            <Outlet />
        </DashboardLayout>
    );
};

export default AdminDashboard;
