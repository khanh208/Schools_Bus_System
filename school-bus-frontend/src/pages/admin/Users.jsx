import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaUser, FaPlus, FaEdit, FaTrash, FaTimes, FaCheck, FaBan } from 'react-icons/fa';

const Users = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingId, setEditingId] = useState(null);
    
    const initialForm = {
        username: '', email: '', full_name: '', phone: '', role: 'parent', password: ''
    };
    const [formData, setFormData] = useState(initialForm);

    const fetchUsers = async () => {
        try {
            const res = await api.get('/auth/users/');
            setUsers(res.data.results || res.data);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchUsers(); }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingId) {
                // Khi sửa, không gửi password nếu trống
                const { password, ...data } = formData;
                if (password) data.password = password;
                
                await api.patch(`/auth/users/${editingId}/`, data);
                alert("Cập nhật thành công!");
            } else {
                // Khi tạo mới, dùng endpoint register để tự tạo profile (Driver/Parent)
                await api.post('/auth/register/', {
                    ...formData,
                    password_confirm: formData.password // Backend require confirm
                });
                alert("Tạo tài khoản thành công!");
            }
            setShowModal(false);
            fetchUsers();
        } catch (error) {
            alert("Lỗi: " + JSON.stringify(error.response?.data || error.message));
        }
    };

    const toggleStatus = async (user) => {
        try {
            const action = user.is_active ? 'deactivate' : 'activate';
            await api.post(`/auth/users/${user.id}/${action}/`);
            fetchUsers();
        } catch (e) { alert("Lỗi đổi trạng thái"); }
    };

    const openModal = (user = null) => {
        if (user) {
            setFormData({
                username: user.username,
                email: user.email,
                full_name: user.full_name,
                phone: user.phone || '',
                role: user.role,
                password: '' // Reset pass field
            });
            setEditingId(user.id);
        } else {
            setFormData(initialForm);
            setEditingId(null);
        }
        setShowModal(true);
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-800">Quản lý Tài khoản</h2>
                <button onClick={() => openModal()} className="bg-blue-600 text-white px-4 py-2 rounded flex items-center gap-2">
                    <FaPlus /> Tạo tài khoản
                </button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 uppercase text-xs text-gray-500">
                        <tr>
                            <th className="p-3">Username</th>
                            <th className="p-3">Họ tên</th>
                            <th className="p-3">Vai trò</th>
                            <th className="p-3">Trạng thái</th>
                            <th className="p-3 text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y">
                        {users.map(user => (
                            <tr key={user.id} className="hover:bg-gray-50">
                                <td className="p-3 font-medium">{user.username}</td>
                                <td className="p-3">
                                    <div>{user.full_name}</div>
                                    <div className="text-xs text-gray-400">{user.email}</div>
                                </td>
                                <td className="p-3">
                                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${
                                        user.role === 'admin' ? 'bg-red-100 text-red-700' :
                                        user.role === 'driver' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                                    }`}>{user.role}</span>
                                </td>
                                <td className="p-3">
                                    <button onClick={() => toggleStatus(user)} className={`flex items-center gap-1 text-xs font-bold px-2 py-1 rounded ${
                                        user.is_active ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-500'
                                    }`}>
                                        {user.is_active ? <><FaCheck/> Active</> : <><FaBan/> Inactive</>}
                                    </button>
                                </td>
                                <td className="p-3 text-right">
                                    <button onClick={() => openModal(user)} className="text-blue-600 hover:bg-blue-50 p-2 rounded"><FaEdit/></button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            
            {/* Modal Form (Giản lược) */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white p-6 rounded-lg w-full max-w-md shadow-xl">
                        <h3 className="font-bold text-lg mb-4">{editingId ? 'Sửa tài khoản' : 'Tạo tài khoản mới'}</h3>
                        <form onSubmit={handleSubmit} className="space-y-3">
                            <input className="border p-2 w-full rounded" placeholder="Username" required disabled={!!editingId}
                                value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} />
                            <input className="border p-2 w-full rounded" placeholder="Email" required type="email"
                                value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                            <input className="border p-2 w-full rounded" placeholder="Họ và tên" required
                                value={formData.full_name} onChange={e => setFormData({...formData, full_name: e.target.value})} />
                            <select className="border p-2 w-full rounded" value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})}>
                                <option value="parent">Phụ huynh</option>
                                <option value="driver">Tài xế</option>
                                <option value="admin">Admin</option>
                            </select>
                            <input className="border p-2 w-full rounded" placeholder={editingId ? "Mật khẩu mới (để trống nếu không đổi)" : "Mật khẩu (*)"} 
                                type="password" required={!editingId}
                                value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} />
                            
                            <div className="flex justify-end gap-2 mt-4">
                                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-gray-600">Hủy</button>
                                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">Lưu</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Users;