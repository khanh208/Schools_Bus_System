import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaMapMarkedAlt, FaPlus, FaEdit, FaTrash, FaTimes } from 'react-icons/fa';

const Areas = () => {
    const [areas, setAreas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [formData, setFormData] = useState({ name: '', description: '' });

    const fetchAreas = async () => {
        try {
            const res = await api.get('/students/areas/');
            setAreas(res.data.results || res.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchAreas(); }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingId) {
                await api.patch(`/students/areas/${editingId}/`, formData);
            } else {
                await api.post('/students/areas/', formData);
            }
            fetchAreas();
            setShowModal(false);
            setFormData({ name: '', description: '' });
            setEditingId(null);
        } catch (error) {
            alert("Lỗi lưu dữ liệu");
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm("Xóa khu vực này?")) {
            await api.delete(`/students/areas/${id}/`);
            fetchAreas();
        }
    };

    const openModal = (area = null) => {
        if (area) {
            setFormData({ name: area.name, description: area.description || '' });
            setEditingId(area.id);
        } else {
            setFormData({ name: '', description: '' });
            setEditingId(null);
        }
        setShowModal(true);
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between mb-6">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <FaMapMarkedAlt className="text-blue-600"/> Quản lý Khu vực
                </h2>
                <button onClick={() => openModal()} className="bg-green-600 text-white px-4 py-2 rounded flex items-center gap-2">
                    <FaPlus /> Thêm Khu vực
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {areas.map(area => (
                    <div key={area.id} className="border p-4 rounded-lg hover:shadow-md bg-gray-50 relative group">
                        <h3 className="font-bold text-lg">{area.name}</h3>
                        <p className="text-gray-500 text-sm">{area.description || 'Không có mô tả'}</p>
                        <div className="mt-2 text-xs bg-blue-100 text-blue-800 inline-block px-2 py-1 rounded">
                            {area.student_count || 0} học sinh
                        </div>
                        
                        <div className="absolute top-3 right-3 hidden group-hover:flex gap-2">
                            <button onClick={() => openModal(area)} className="text-blue-600"><FaEdit /></button>
                            <button onClick={() => handleDelete(area.id)} className="text-red-600"><FaTrash /></button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg w-96">
                        <div className="flex justify-between mb-4">
                            <h3 className="font-bold">{editingId ? 'Sửa Khu vực' : 'Thêm Khu vực'}</h3>
                            <button onClick={() => setShowModal(false)}><FaTimes /></button>
                        </div>
                        <form onSubmit={handleSubmit} className="space-y-3">
                            <input className="w-full border p-2 rounded" placeholder="Tên khu vực (VD: Quận 1)" required
                                value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                            <textarea className="w-full border p-2 rounded" placeholder="Mô tả"
                                value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
                            <button className="w-full bg-blue-600 text-white py-2 rounded font-bold">Lưu</button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Areas;