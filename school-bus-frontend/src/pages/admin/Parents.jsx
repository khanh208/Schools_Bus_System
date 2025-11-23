import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaUsers, FaChild, FaPhoneAlt, FaMapMarkerAlt, FaPlus, FaEdit, FaTrash, FaTimes, FaUser } from 'react-icons/fa';

const Parents = () => {
    const [parents, setParents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [isCreating, setIsCreating] = useState(false);
    const [editingParent, setEditingParent] = useState(null);

    // Form state
    const initialForm = {
        // User fields (Chỉ dùng khi tạo mới)
        username: '',
        password: '',
        email: '',
        full_name: '',
        phone: '',
        
        // Parent fields
        address: '',
        emergency_contact: ''
    };
    const [formData, setFormData] = useState(initialForm);

    const fetchData = async () => {
        try {
            const res = await api.get('/auth/parents/');
            setParents(res.data.results || res.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    // Mở modal Tạo mới
    const handleCreate = () => {
        setIsCreating(true);
        setEditingParent(null);
        setFormData(initialForm);
        setShowModal(true);
    };

    // Mở modal Sửa
    const handleEdit = (parent) => {
        setIsCreating(false);
        setEditingParent(parent);
        setFormData({
            ...initialForm,
            address: parent.address,
            emergency_contact: parent.emergency_contact,
            // Điền sẵn thông tin user để hiển thị (không sửa được username/password ở đây)
            full_name: parent.user.full_name,
            phone: parent.user.phone
        });
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (isCreating) {
                // Gọi API đăng ký User mới với role='parent'
                await api.post('/auth/register/', {
                    ...formData,
                    role: 'parent',
                    password_confirm: formData.password
                });
                alert("Thêm phụ huynh thành công!");
            } else {
                // Gọi API cập nhật hồ sơ Parent
                await api.patch(`/auth/parents/${editingParent.id}/`, {
                    address: formData.address,
                    emergency_contact: formData.emergency_contact
                });
                alert("Cập nhật thành công!");
            }
            setShowModal(false);
            fetchData();
        } catch (error) {
            alert("Lỗi: " + JSON.stringify(error.response?.data || error.message));
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm("Bạn có chắc muốn xóa phụ huynh này? Tài khoản đăng nhập và liên kết học sinh sẽ bị ảnh hưởng.")) {
            try {
                await api.delete(`/auth/parents/${id}/`);
                fetchData();
            } catch (e) { alert("Xóa thất bại"); }
        }
    };

    return (
        <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <FaUsers className="text-blue-600" /> Danh sách Phụ huynh
                </h2>
                <div className="flex gap-2">
                    <button onClick={fetchData} className="text-blue-600 hover:underline text-sm px-3">Làm mới</button>
                    <button onClick={handleCreate} className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2 shadow">
                        <FaPlus /> Thêm Phụ huynh
                    </button>
                </div>
            </div>
            
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 text-gray-700 text-sm uppercase">
                        <tr>
                            <th className="px-6 py-3 font-bold">Họ tên / Email</th>
                            <th className="px-6 py-3 font-bold">Liên hệ</th>
                            <th className="px-6 py-3 font-bold">Địa chỉ</th>
                            <th className="px-6 py-3 font-bold text-center">Số con</th>
                            <th className="px-6 py-3 font-bold">Khẩn cấp</th>
                            <th className="px-6 py-3 font-bold text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody className="text-gray-600 text-sm divide-y divide-gray-100">
                        {loading ? (
                            <tr><td colSpan="6" className="text-center py-8">Đang tải...</td></tr>
                        ) : parents.map((parent) => (
                            <tr key={parent.id} className="hover:bg-gray-50 group">
                                <td className="px-6 py-4">
                                    <div className="font-bold text-gray-900 flex items-center gap-2">
                                        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-500">
                                            <FaUser size={12} />
                                        </div>
                                        {parent.user.full_name}
                                    </div>
                                    <div className="text-xs text-blue-500 mt-1 ml-10">{parent.user.email}</div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <FaPhoneAlt className="text-gray-400 text-xs" />
                                        {parent.user.phone}
                                    </div>
                                </td>
                                <td className="px-6 py-4 max-w-xs truncate" title={parent.address}>
                                    <div className="flex items-center gap-2">
                                        <FaMapMarkerAlt className="text-gray-400" />
                                        <span className="truncate">{parent.address}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-blue-50 text-blue-700 font-bold text-xs">
                                        <FaChild className="mr-1" /> {parent.children_count}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-red-500 font-medium bg-red-50 px-2 py-1 rounded text-xs">
                                        {parent.emergency_contact}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button onClick={() => handleEdit(parent)} className="p-2 text-blue-600 hover:bg-blue-50 rounded" title="Sửa">
                                            <FaEdit />
                                        </button>
                                        <button onClick={() => handleDelete(parent.id)} className="p-2 text-red-600 hover:bg-red-50 rounded" title="Xóa">
                                            <FaTrash />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* MODAL FORM */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[1100] p-4">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg animate-[fadeIn_0.2s] overflow-hidden">
                        <div className="p-4 border-b flex justify-between items-center bg-gray-50">
                            <h3 className="font-bold text-lg text-gray-800">{isCreating ? 'Thêm Phụ huynh Mới' : 'Cập nhật Phụ huynh'}</h3>
                            <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600"><FaTimes size={20}/></button>
                        </div>
                        
                        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
                            
                            {/* Phần tạo User (Chỉ hiện khi thêm mới) */}
                            {isCreating && (
                                <div className="space-y-4 border-b pb-4 mb-4 border-dashed">
                                    <p className="text-xs font-bold text-blue-600 uppercase tracking-wide">Thông tin tài khoản</p>
                                    <div className="grid grid-cols-2 gap-4">
                                        <input className="border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Tên đăng nhập (*)" required 
                                            value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} />
                                        <input className="border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Mật khẩu (*)" type="password" required 
                                            value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <input className="border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Họ và tên (*)" required 
                                            value={formData.full_name} onChange={e => setFormData({...formData, full_name: e.target.value})} />
                                        <input className="border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Email (*)" type="email" required 
                                            value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                                    </div>
                                    <input className="border p-2 rounded w-full focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Số điện thoại" 
                                        value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} />
                                </div>
                            )}

                            {/* Phần thông tin bổ sung */}
                            <p className="text-xs font-bold text-green-600 uppercase tracking-wide">Thông tin liên hệ</p>
                            
                            <div>
                                <label className="block text-sm text-gray-600 mb-1">Địa chỉ nhà (*)</label>
                                <input className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none" required
                                    value={formData.address} onChange={e => setFormData({...formData, address: e.target.value})} 
                                    placeholder="VD: 123 Đường Lê Lợi, Quận 1..."
                                />
                            </div>

                            <div>
                                <label className="block text-sm text-gray-600 mb-1">Số liên hệ khẩn cấp (*)</label>
                                <input className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none" required
                                    value={formData.emergency_contact} onChange={e => setFormData({...formData, emergency_contact: e.target.value})} 
                                    placeholder="VD: 0909xxxxxx (Người thân)"
                                />
                            </div>

                            <button type="submit" className="w-full bg-blue-600 text-white py-3 rounded-xl font-bold hover:bg-blue-700 shadow-lg mt-4">
                                {isCreating ? 'Tạo Phụ huynh' : 'Lưu Thay Đổi'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Parents;