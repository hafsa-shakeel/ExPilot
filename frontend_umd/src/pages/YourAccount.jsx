import React, { useEffect, useState } from 'react';
import API from '../api';
import { toast } from 'react-toastify';

const YourAccount = () => {
    const [business, setBusiness] = useState(null);
    const [editMode, setEditMode] = useState(false);
    const [formData, setFormData] = useState({
        business_name: '',
        industry: '',
        contact_person: ''
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchBusinessInfo();
    }, []);

    const fetchBusinessInfo = async () => {
        setLoading(true);
        try {
            const res = await API.post(
                '/business/get-business',
                {},
                { withCredentials: true }
            );
            const data = res.data.business_info;
            setBusiness(data);
            setFormData({
                business_name: data.business_name || '',
                industry: data.industry || '',
                contact_person: data.contact_person || ''
            });
        } catch (err) {
            console.error('Error fetching business:', err);
            toast.error('Failed to load business info.');
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleUpdate = async () => {
        if (!business?.business_id) return;
        try {
            await API.patch(
                `/business/update-business/${business.business_id}`,
                formData,
                { withCredentials: true }
            );
            toast.success("Business updated successfully!");
            setEditMode(false);
            fetchBusinessInfo();
        } catch (err) {
            console.error('Update failed:', err);
            toast.error("Update failed. Please try again.");
        }
    };

    const handleDeactivate = async () => {
        if (!business?.business_id) return;
        try {
            await API.delete(
                `/business/delete/${business.business_id}`,
                { withCredentials: true }
            );
            toast.success("Business deactivated successfully.");
            fetchBusinessInfo();
        } catch (err) {
            console.error('Deactivate failed:', err);
            toast.error("Deactivation failed. Please try again.");
        }
    };

    const handleReactivate = async () => {
        if (!business?.business_id) return;
        try {
            await API.patch(
                `/business/reactivate-business/${business.business_id}`,
                {},
                { withCredentials: true }
            );
            toast.success("Business reactivated successfully.");
            fetchBusinessInfo();
        } catch (err) {
            console.error('Reactivate failed:', err);
            toast.error("Reactivation failed. Please try again.");
        }
    };

    if (loading) return <p>Loading business data...</p>;

    return (
        <div className="container mt-4 px-4">
            <style>{`
                .btn-prussian {
                    color: #003153;
                    border: 1px solid #003153;
                    background-color: transparent;
                    transition: all 0.3s ease;
                }
                .btn-prussian:hover {
                    background-color: #003153;
                    color: white;
                }
            `}</style>

            <div className="card shadow-sm p-4 mb-4 bg-white rounded border-0">
                <h3 className="mb-4 border-bottom pb-2">My Business Account</h3>
                {!editMode ? (
                    <div>
                        <p><strong>Business Name:</strong> {business.business_name}</p>
                        <p><strong>Industry:</strong> <span className="text-muted">{business.industry}</span></p>
                        <p><strong>Email:</strong> <span className="text-muted">{business.email}</span></p>
                        <p><strong>Contact Person:</strong> {business.contact_person}</p>
                        <p><strong>Created At:</strong> {new Date(business.created_at).toLocaleString()}</p>
                        <p><strong>Status:</strong>
                            {business.status ? (
                                <span className="badge bg-success ms-2">Active</span>
                            ) : (
                                <span className="badge bg-danger ms-2">Inactive</span>
                            )}
                        </p>

                        <div className="mt-4">
                            {business.status ? (
                                <>
                                    <button className="btn btn-prussian me-2" onClick={() => setEditMode(true)}>Update</button>
                                    <button className="btn btn-outline-danger" onClick={handleDeactivate}>Deactivate Business</button>
                                </>
                            ) : (
                                <button className="btn btn-outline-success" onClick={handleReactivate}>Reactivate Business</button>
                            )}
                        </div>
                    </div>
                ) : (
                    <div>
                        <div className="mb-3">
                            <label className="form-label">Business Name</label>
                            <input
                                type="text"
                                name="business_name"
                                className="form-control"
                                value={formData.business_name}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="mb-3">
                            <label className="form-label">Industry</label>
                            <input
                                type="text"
                                name="industry"
                                className="form-control"
                                value={formData.industry}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="mb-3">
                            <label className="form-label">Contact Person</label>
                            <input
                                type="text"
                                name="contact_person"
                                className="form-control"
                                value={formData.contact_person}
                                onChange={handleChange}
                            />
                        </div>

                        <button
                            className="btn btn-success me-2"
                            onClick={handleUpdate}>
                            Save
                        </button>
                        <button
                            className="btn btn-secondary"
                            onClick={() => setEditMode(false)}>
                            Cancel
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default YourAccount;
