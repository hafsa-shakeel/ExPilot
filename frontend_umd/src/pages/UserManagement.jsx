import React, { useEffect, useState } from 'react';
import API from '../api';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const UserManagement = () => {
    const [users, setUsers] = useState([]);
    const [page, setPage] = useState(1);
    const [limit] = useState(3);
    const [totalPages, setTotalPages] = useState(1);
    const [refresh, setRefresh] = useState(false);

    const [form, setForm] = useState({
        username: '',
        email: '',
        contact_no: '',
        password: '',
        role_id: 2,
        //business_id: null // add this to track
    });

    const [editingUser, setEditingUser] = useState(null);

    useEffect(() => {
        fetchUsers();
        API.get('/auth/me', { withCredentials: true })
            .catch(() => toast.error('Failed to fetch user info'));
    }, [page, refresh]);

    const fetchUsers = async () => {
        try {
            const res = await API.get(`/auth/users?page=${page}&limit=${limit}`, { withCredentials: true });
            setUsers(res.data.users);
            setTotalPages(res.data.total_pages);
        } catch (error) {
            toast.error("Failed to load users");
        }
    };

    const handleDelete = async (user_id) => {
        try {
            await API.delete(`/auth/delete-user/${user_id}`, { withCredentials: true });
            toast.success("User deleted");
            setRefresh(prev => !prev);
        } catch (error) {
            toast.error(error.response?.data?.error || "Delete failed");
        }
    };

    const handleSubmit = async () => {
        console.log("Submitting user with payload:", form);

        try {
            if (editingUser) {
                await API.put(`/auth/update-user/${editingUser.user_id}`, form, { withCredentials: true });
                toast.success("User updated");
            } else {
                await API.post('/auth/add-user', form, { withCredentials: true });
                toast.success("User added");
            }

            setForm({
                username: '',
                email: '',
                contact_no: '',
                password: '',
                role_id: 2,
            });
            setEditingUser(null);
            setRefresh(prev => !prev);
        } catch (error) {
            toast.error(error.response?.data?.error || "Operation failed");
        }
    };

    const startEdit = (user) => {
        setEditingUser(user);
        setForm(prev => ({
            ...prev,
            username: user.username,
            email: user.email,
            contact_no: user.contact_no,
            password: '',
            role_id: user.role_id
        }));
    };

    return (
        <div className="container mt-4">
            <h3 className="mb-3">User Management</h3>

            <div className="card p-4 mb-4">
                <h5>{editingUser ? "Edit User" : "Add User"}</h5>
                {(
                    <div className="mb-2">
                        <input className="form-control mb-2" placeholder="Username" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} />
                    </div>
                )}
                <input className="form-control mb-2" placeholder="Email" value={form.email} disabled={!!editingUser} onChange={e => setForm({ ...form, email: e.target.value })} />
                <input className="form-control mb-2" placeholder="Contact No" value={form.contact_no} onChange={e => setForm({ ...form, contact_no: e.target.value })} />
                <input className="form-control mb-2" type="password" placeholder="Password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
                <div className="mb-2">
                    <label className="form-label">Role: Branch Manager</label>
                </div>
                <div className="d-flex gap-2">
                    <button
                        className="btn"
                        style={{
                            backgroundColor: '#003153', color: 'white'
                        }} onClick={handleSubmit} > {editingUser ? "Update" : "Add"}</button>
                    {editingUser && (<button className="btn btn-secondary" onClick={() => {
                        setEditingUser(null);
                        setForm({
                            username: '',
                            email: '',
                            contact_no: '',
                            password: '',
                            role_id: 2
                        });
                    }} >Cancel</button>
                    )}
                </div>


            </div>

            <table className="table table-bordered">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Contact</th>
                        <th>Role</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {users.map(user => (
                        <tr key={user.user_id}>
                            <td>{user.user_id}</td>
                            <td>{user.username}</td>
                            <td>{user.email}</td>
                            <td>{user.contact_no}</td>
                            <td>{user.role_id === 1 ? "Admin" : user.role_id === 2 ? "Manager" : "Viewer"}</td>
                            <td>
                                <button className="btn btn-sm me-2" style={{ backgroundColor: '#003153', color: 'white' }}
                                    onClick={() => startEdit(user)}> Edit </button>

                                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(user.user_id)}>Delete</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            <div className="d-flex justify-content-between">
                <button className="btn btn-outline-primary" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button>
                <span>Page {page} of {totalPages}</span>
                <button className="btn btn-outline-primary" disabled={page === totalPages} onClick={() => setPage(page + 1)}>Next</button>
            </div>
        </div>
    );
};

export default UserManagement;