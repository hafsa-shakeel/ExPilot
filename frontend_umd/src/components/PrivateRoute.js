// src/components/PrivateRoute.js
import React from 'react';
import { Navigate } from 'react-router-dom';

const PrivateRoute = ({ children, allowedRoles }) => {
    const roleId = parseInt(sessionStorage.getItem('role_id'));

    if (!roleId) {
        return <Navigate to="/" />;
    }

    if (!allowedRoles.includes(roleId)) {
        return <Navigate to="/" />;
    }

    return children;
};

export default PrivateRoute;
