import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaChalkboardTeacher, FaPlus, FaEdit, FaTrash, FaTimes } from 'react-icons/fa';

const Classes = () => {
    const [classes, setClasses] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [editingId, setEditingId] = useState(null);
    
    const initialForm = { name: '', grade_level: 1, academic_year: '2024-2025', teacher_name: '', room_number: '' };
    const [formData, setFormData] = useState(initialForm);

    const fetchClasses = async () => {
        const res = await api.get('/students/classes/');
        setClasses(res.data.results || res.data);
    };

    useEffect(() => { fetchClasses(); }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingId) await api.patch(`/students/classes/${editingId}/`, formData);
            else await api.post('/students/classes/', formData);
            
            fetchClasses();
            setShowModal(false);
        } catch (error) { alert("Lỗi lưu dữ liệu"); }
    };

    const handleDelete = async (id) => {
        if (window.confirm("Xóa lớp này?")) {
            await api.delete(`/students/classes/${id}/`);
            fetchClasses();
        }
    };

    const openModal = (cls = null) => {
        if (cls) {
            setFormData(cls);
            setEditingId(cls.id);
        } else {
            setFormData(initialForm);
            setEditingId(null);
        }
        setShowModal(true);
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between mb-6">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <FaChalkboardTeacher className="text-orange-500"/> Quản lý Lớp học
                </h2>
                <button onClick={() => openModal()} className="bg-green-600 text-white px-4 py-2 rounded flex gap-2">
                    <FaPlus /> Thêm Lớp
                </button>
            </div>

            <table className="w-full text-left">
                <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                    <tr>
                        <th className="p-3">Tên lớp</th>
                        <th className="p-3">Khối</th>
                        <th className="p-3">GVCN</th>
                        <th className="p-3">Phòng</th>
                        <th className="p-3 text-right">Hành động</th>
                    </tr>
                </thead>
                <tbody className="divide-y">
                    {classes.map(cls => (
                        <tr key={cls.id} className="hover:bg-gray-50">
                            <td className="p-3 font-bold">{cls.name}</td>
                            <td className="p-3">{cls.grade_level}</td>
                            <td className="p-3">{cls.teacher_name}</td>
                            <td className="p-3">{cls.room_number}</td>
                            <td className="p-3 text-right flex justify-end gap-2">
                                <button onClick={() => openModal(cls)} className="text-blue-600"><FaEdit/></button>
                                <button onClick={() => handleDelete(cls.id)} className="text-red-600"><FaTrash/></button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg w-96">
                        <div className="flex justify-between mb-4">
                            <h3 className="font-bold">{editingId ? 'Sửa Lớp' : 'Thêm Lớp'}</h3>
                            <button onClick={() => setShowModal(false)}><FaTimes /></button>
                        </div>
                        <form onSubmit={handleSubmit} className="space-y-3">
                            <div className="grid grid-cols-2 gap-2">
                                <input className="border p-2 rounded" placeholder="Tên lớp (1A)" required
                                    value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                                <input type="number" className="border p-2 rounded" placeholder="Khối" required
                                    value={formData.grade_level} onChange={e => setFormData({...formData, grade_level: e.target.value})} />
                            </div>
                            <input className="w-full border p-2 rounded" placeholder="Giáo viên chủ nhiệm"
                                value={formData.teacher_name} onChange={e => setFormData({...formData, teacher_name: e.target.value})} />
                            <input className="w-full border p-2 rounded" placeholder="Phòng học"
                                value={formData.room_number} onChange={e => setFormData({...formData, room_number: e.target.value})} />
                            <button className="w-full bg-blue-600 text-white py-2 rounded font-bold">Lưu</button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Classes;