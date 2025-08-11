import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import LoginPage from './pages/LoginPage';
import RegisterBusiness from './pages/RegisterBusiness';
import SuperAdminDashboard from './pages/SuperAdminDashboard';
import AdminDashboard from './pages/AdminDashboard';
import BranchManagerDashboard from './pages/BranchManagerDashboard'
import PrivateRoute from './components/PrivateRoute';

//admin
import Overview from './pages/Overview';
import YourAccount from './pages/YourAccount';
import UserManagement from './pages/UserManagement';
import ManageBranches from './pages/ManageBranches';
import BudgetManagement from './pages/BudgetManagement';
import Alerts from './pages/Alerts';
import ExpenseManagement from './pages/ExpenseManagement';

//manager
import BranchOverview from './pages/BranchOverview';
import ManageBranch from './pages/ManageBranch';
import Managerbudgetmanagement from './pages/Managerbudgetmanagement';

const HomeRedirect = ({ onLogout }) => {
  const navigate = useNavigate();
  const roleId = sessionStorage.getItem("role_id");

  useEffect(() => {
    if (roleId === "3") {
      navigate("/dashboard/superadmin");
    } else if (roleId === "1") {
      navigate("/dashboard/admin");
    } else if (roleId === "2") {
      navigate("/dashboard/manager");
    }
  }, [roleId, navigate]);

  return (
    <div className="container mt-5">
      <h2>Welcome</h2>
      <p><strong>Username:</strong> {sessionStorage.getItem("username")}</p>
      <p><strong>Business ID:</strong> {sessionStorage.getItem("business_id")}</p>
      <p>
        <strong>Role:</strong>{" "}
        {roleId === "1" ? "Admin" : roleId === "2" ? "Branch Manager" : "Super Admin"}
      </p>
      <button className="btn btn-danger" onClick={onLogout}>
        Logout
      </button>
    </div>
  );
};

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!sessionStorage.getItem("role_id"));

  const handleLogout = () => {
    sessionStorage.clear();
    setIsLoggedIn(false);
    fetch('http://localhost:5000/api/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });
  };

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route
          path="/"
          element={
            !isLoggedIn ? (
              <LoginPage onLogin={() => setIsLoggedIn(true)} />
            ) : (
              <HomeRedirect onLogout={handleLogout} />
            )
          }
        />

        <Route path="/register-business" element={<RegisterBusiness />} />

        {/* Super Admin Dashboard */}
        <Route
          path="/dashboard/superadmin"
          element={
            <PrivateRoute allowedRoles={[3]}>
              <SuperAdminDashboard />
            </PrivateRoute>
          }
        />

        {/* Admin Dashboard with nested layout */}
        <Route
          path="/dashboard/admin"
          element={
            <PrivateRoute allowedRoles={[1]}>
              <AdminDashboard />
            </PrivateRoute>
          }
        >
          {/* NESTED ROUTES inside AdminDashboard */}
          <Route index element={<Overview />} />
          <Route path="your-account" element={<YourAccount />} />
          <Route path="admin/users" element={<UserManagement />} />
          <Route path="admin/branches" element={< ManageBranches />} />
          <Route path="admin/budgetmanagement" element={< BudgetManagement />} />
          <Route path="admin/expensemanagement" element={< ExpenseManagement />} />
          <Route path="admin/alerts" element={< Alerts />} />



        </Route>

        <Route
          path="/dashboard/manager"
          element={
            <PrivateRoute allowedRoles={[2]}>
              <BranchManagerDashboard />
            </PrivateRoute>
          }
        >
          {/* NESTED ROUTES inside managerDashboard */}
          <Route index element={<BranchOverview />} />
          <Route path="manage-branch" element={< ManageBranch />} />
          <Route path="managerbudgetmanagement" element={< Managerbudgetmanagement />} />
          <Route path="expensemanagement" element={< ExpenseManagement />} />
          <Route path="alerts" element={< Alerts />} />


        </Route>


        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>

      <ToastContainer position="bottom-right" theme="colored" autoClose={3000} />
    </Router>
  );
}

export default App;
