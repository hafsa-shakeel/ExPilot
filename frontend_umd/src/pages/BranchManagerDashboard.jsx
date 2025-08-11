import React from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { Outlet } from 'react-router-dom';

const BranchManagerDashboard = () => {
    return (
        <DashboardLayout dashboardType="Manager">
            <Outlet />
        </DashboardLayout>
    );
};

export default BranchManagerDashboard;
