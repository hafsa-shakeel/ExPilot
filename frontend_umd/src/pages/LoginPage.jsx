import React, { useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import API from '../api';

const LoginPage = ({ onLogin }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        try {
            const response = await API.post('/auth/login',
                { email, password },
                {
                    headers: { 'Content-Type': 'application/json' },
                    withCredentials: true
                }
            );

            const { user } = response.data;
            sessionStorage.setItem('role_id', user.role_id);
            sessionStorage.setItem('user_id', user.user_id);
            sessionStorage.setItem('username', user.username);
            sessionStorage.setItem('business_id', user.business_id);
            sessionStorage.setItem('branch_id', user.branch_id || '');

            onLogin();
        } catch (err) {
            setError(err.response?.data?.error || 'Login failed');
        }
    };

    return (
        <div style={{ backgroundColor: "#D1E5F4", minHeight: "100vh" }}>
            <div className="d-flex justify-content-center align-items-center min-vh-100 px-3">
                <div className="card shadow p-4 mx-auto" style={{ maxWidth: '90%', width: '500px' }}>
                    <div className="d-flex flex-column align-items-center mb-1">
                        <img src="/logo.png" alt="UMD Logo" style={{
                            borderRadius: "10%",
                            width: "56px",
                            height: "56px",
                            objectFit: "cover",
                            border: "0px solid #003153", marginBottom: "10px"
                        }} />
                        <h2 className="fw-bold" style={{ fontSize: "1.6rem", letterSpacing: "1.4px", color: '#003153', textShadow: "0 5px 9px rgba(4, 35, 58, 0.13)" }} >Welcome to ExPilot</h2>
                        <p className="text-muted">Sign in to your account</p>  </div>
                    {error && <div className="alert alert-danger">{error}</div>}
                    <form onSubmit={handleSubmit}>
                        <div className="mb-3">
                            <label className="form-label">Email</label>
                            <input type="email" className="form-control" value={email} onChange={(e) => setEmail(e.target.value)} required />
                        </div>
                        <div className="mb-3">
                            <label className="form-label">Password</label>
                            <input type="password" className="form-control" value={password} onChange={(e) => setPassword(e.target.value)} required />
                        </div>
                        <button type="submit" className="btn w-100" style={{ backgroundColor: '#003153', color: 'white', border: 'none' }}>
                            Sign In
                        </button>
                    </form>
                    <p className="text-center mt-3">
                        Don't have an account? <Link to="/register-business">Register your business</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
