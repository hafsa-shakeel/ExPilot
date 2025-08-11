// src/pages/RegisterBusiness.js
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const RegisterBusiness = () => {
    const navigate = useNavigate();

    const [formData, setFormData] = useState({
        business_name: '',
        industry: '',
        contact_person: '',
        username: '',
        user_email: '',
        contact_no: '',
        password: ''
    });

    const [message, setMessage] = useState('');

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('');

        // Basic validations
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.user_email)) {
            setMessage("Please enter a valid email address.");
            return;
        }

        if (formData.password.length < 6) {
            setMessage("Password must be at least 6 characters long.");
            return;
        }

        if (!/^\d{10,15}$/.test(formData.contact_no)) {
            setMessage("Contact number should be 10 to 15 digits.");
            return;
        }

        // Check for missing fields
        const requiredFields = [
            'business_name', 'industry', 'contact_person',
            'contact_no', 'username', 'user_email', 'password'
        ];
        for (let field of requiredFields) {
            if (!formData[field]) {
                setMessage("All fields are required.");
                return;
            }
        }

        // Submit to backend
        try {
            const response = await axios.post("http://localhost:5000/api/auth/register-business", formData);
            setMessage("We have received your request! Wait till we approve it.");
            setFormData({
                business_name: '',
                industry: '',
                contact_person: '',
                contact_no: '',
                username: '',
                user_email: '',
                password: ''
            });
        } catch (error) {
            if (error.response && error.response.data && error.response.data.error) {
                setMessage("Registration failed: " + error.response.data.error);
            } else {
                setMessage("Registration failed. Try again.");
            }
        }
    };

    return (
        <div className="container mt-5">
            <h2 className="mb-4">Register Business</h2>
            {message && <div className="alert alert-info">{message}</div>}
            <form onSubmit={handleSubmit}>
                <div className="row">
                    <div className="mb-3 col-md-6">
                        <label className="form-label">Business Name</label>
                        <input type="text" className="form-control" name="business_name" value={formData.business_name} onChange={handleChange} required />
                    </div>
                    <div className="mb-3 col-md-6">
                        <label className="form-label">Industry</label>
                        <input type="text" className="form-control" name="industry" value={formData.industry} onChange={handleChange} required />
                    </div>
                </div>

                <div className="row">
                    <div className="mb-3 col-md-6">
                        <label className="form-label">Contact Person</label>
                        <input type="text" className="form-control" name="contact_person" value={formData.contact_person} onChange={handleChange} required />
                    </div>
                    <div className="mb-3 col-md-6">
                        <label className="form-label">Contact Number</label>
                        <input type="text" className="form-control" name="contact_no" value={formData.contact_no} onChange={handleChange} required />
                    </div>
                </div>

                <div className="row">
                    <div className="mb-3 col-md-6">
                        <label className="form-label">Admin Username</label>
                        <input type="text" className="form-control" name="username" value={formData.username} onChange={handleChange} required />
                    </div>
                    <div className="mb-3 col-md-6">
                        <label className="form-label">Admin Email</label>
                        <input type="email" className="form-control" name="user_email" value={formData.user_email} onChange={handleChange} required />
                    </div>
                </div>

                <div className="mb-3">
                    <label className="form-label">Password</label>
                    <input type="password" className="form-control" name="password" value={formData.password} onChange={handleChange} required />
                </div>

                <button type="submit" className="btn btn-primary">Register Business</button>
                <button type="button" className="btn btn-secondary ms-2" onClick={() => navigate('/')}>Back to Login</button>
            </form>
        </div>
    );
};

export default RegisterBusiness;
