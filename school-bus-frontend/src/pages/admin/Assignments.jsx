import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaExchangeAlt, FaPlus, FaEdit, FaTrash, FaTimes, FaSearch } from 'react-icons/fa';

const Assignments = () => {
    const [assignments, setAssignments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingId, setEditingId] = useState(null);

    // Data cho dropdown
    const [students, setStudents] = useState([]);
    const [routes, setRoutes] = useState([]);
    const [stops, setStops] = useState([]); // Điểm dừng của tuyến đang chọn

    const initialForm = {
        student: '',
        route: '',
        stop: '',
        assignment_type: 'both',
        start_date: new Date().toISOString().split('T')[0],
        is_active: true
    };
    const [formData, setFormData] = useState(initialForm);

    // 1. Tải dữ liệu ban đầu
    const fetchData = async () => {
        try {
            const [resAssign, resStudents, resRoutes] = await Promise.all([
                api.get('/routes/assignments/'),
                api.get('/students/students/?is_active=true'),
                api.get('/routes/routes/?is_active=true')
            ]);
            setAssignments(resAssign.data.results || resAssign.data);
            setStudents(resStudents.data.results || resStudents.data);
            setRoutes(resRoutes.data.results || resRoutes.data);
        } catch (error) {
            console.error("Lỗi tải dữ liệu:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    // 2. Khi chọn Tuyến -> Tải danh sách điểm dừng của tuyến đó
    const handleRouteChange = async (routeId) => {
        setFormData(prev => ({ ...prev, route: routeId, stop: '' })); // Reset điểm dừng cũ
        if (!routeId) {
            setStops([]);
            return;
        }
        try {
            const res = await api.get(`/routes/routes/${routeId}/stops/`);
            setStops(res.data);
        } catch (error) {
            console.error("Lỗi tải điểm dừng:", error);
        }
    };

    // 3. Xử lý Submit
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingId) {
                await api.patch(`/routes/assignments/${editingId}/`, formData);
                alert("Cập nhật thành công!");
            } else {
                await api.post('/routes/assignments/', formData);
                alert("Phân công thành công!");
            }
            setShowModal(false);
            fetchData();
        } catch (error) {
            alert("Lỗi: " + JSON.stringify(error.response?.data || error.message));
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm("Hủy phân công này?")) {
            try {
                await api.delete(`/routes/assignments/${id}/`);
                fetchData();
            } catch (e) { alert("Xóa thất bại"); }
        }
    };

    const openModal = async (item = null) => {
        if (item) {
            // Nếu sửa, cần load điểm dừng của tuyến cũ trước
            await handleRouteChange(item.route); 
            setFormData({
                student: item.student,
                route: item.route,
                stop: item.stop,
                assignment_type: item.assignment_type,
                start_date: item.start_date,
                is_active: item.is_active
            });
            setEditingId(item.id);
        } else {
            setFormData(initialForm);
            setStops([]);
            setEditingId(null);
        }
        setShowModal(true);
    };

    const getTypeBadge = (type) => {
        const map = {
            'pickup': { color: 'bg-blue-100 text-blue-700', label: 'Đón' },
            'dropoff': { color: 'bg-orange-100 text-orange-700', label: 'Trả' },
            'both': { color: 'bg-purple-100 text-purple-700', label: 'Cả hai' }
        };
        const t = map[type] || map['both'];
        return <span className={`px-2 py-1 rounded text-xs font-bold ${t.color}`}>{t.label}</span>;
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <FaExchangeAlt className="text-blue-600"/> Phân công Vận chuyển
                </h2>
                <button onClick={() => openModal()} className="bg-blue-600 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-blue-700 shadow">
                    <FaPlus /> Tạo phân công
                </button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                        <tr>
                            <th className="p-3">Học sinh</th>
                            <th className="p-3">Tuyến xe</th>
                            <th className="p-3">Điểm dừng</th>
                            <th className="p-3">Loại</th>
                            <th className="p-3">Ngày bắt đầu</th>
                            <th className="p-3">Trạng thái</th>
                            <th className="p-3 text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y text-sm">
                        {loading ? <tr><td colSpan="7" className="p-4 text-center">Đang tải...</td></tr> : 
                        assignments.map((item) => (
                            <tr key={item.id} className="hover:bg-gray-50">
                                <td className="p-3">
                                    <div className="font-bold">{item.student_name}</div>
                                    <div className="text-xs text-gray-500">{item.student_code}</div>
                                </td>
                                <td className="p-3 font-medium text-blue-600">{item.route_name}</td>
                                <td className="p-3">{item.stop_name}</td>
                                <td className="p-3">{getTypeBadge(item.assignment_type)}</td>
                                <td className="p-3">{item.start_date}</td>
                                <td className="p-3">
                                    {item.is_active ? 
                                        <span className="text-green-600 font-bold text-xs">✓ Đang chạy</span> : 
                                        <span className="text-gray-400 text-xs">Đã ngưng</span>
                                    }
                                </td>
                                <td className="p-3 text-right">
                                    <button onClick={() => openModal(item)} className="text-blue-600 p-2 hover:bg-blue-50 rounded"><FaEdit/></button>
                                    <button onClick={() => handleDelete(item.id)} className="text-red-600 p-2 hover:bg-red-50 rounded"><FaTrash/></button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[1100] p-4">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden">
                        <div className="p-4 border-b flex justify-between items-center bg-gray-50">
                            <h3 className="font-bold text-lg">{editingId ? 'Sửa Phân công' : 'Phân công Mới'}</h3>
                            <button onClick={() => setShowModal(false)}><FaTimes /></button>
                        </div>
                        
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Học sinh (*)</label>
                                <select className="w-full border p-2 rounded" required
                                    value={formData.student} onChange={e => setFormData({...formData, student: e.target.value})}>
                                    <option value="">-- Chọn học sinh --</option>
                                    {students.map(s => (
                                        <option key={s.id} value={s.id}>{s.full_name} ({s.student_code})</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Tuyến xe (*)</label>
                                <select className="w-full border p-2 rounded" required
                                    value={formData.route} onChange={e => handleRouteChange(e.target.value)}>
                                    <option value="">-- Chọn tuyến --</option>
                                    {routes.map(r => (
                                        <option key={r.id} value={r.id}>{r.route_name} ({r.route_code})</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Điểm đón/trả (*)</label>
                                <select className="w-full border p-2 rounded" required
                                    value={formData.stop} onChange={e => setFormData({...formData, stop: e.target.value})}
                                    disabled={!formData.route} // Khóa nếu chưa chọn tuyến
                                >
                                    <option value="">-- Chọn điểm dừng --</option>
                                    {stops.map(s => (
                                        <option key={s.id} value={s.id}>
                                            {s.stop_order}. {s.stop_name} ({s.estimated_arrival})
                                        </option>
                                    ))}
                                </select>
                                {formData.route && stops.length === 0 && <p className="text-xs text-red-500 mt-1">Tuyến này chưa có điểm dừng nào.</p>}
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Loại</label>
                                    <select className="w-full border p-2 rounded"
                                        value={formData.assignment_type} onChange={e => setFormData({...formData, assignment_type: e.target.value})}>
                                        <option value="pickup">Chỉ Đón</option>
                                        <option value="dropoff">Chỉ Trả</option>
                                        <option value="both">Cả hai</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Ngày bắt đầu</label>
                                    <input type="date" className="w-full border p-2 rounded" required
                                        value={formData.start_date} onChange={e => setFormData({...formData, start_date: e.target.value})} />
                                </div>
                            </div>

                            <button className="w-full bg-blue-600 text-white py-2 rounded font-bold hover:bg-blue-700 mt-2">
                                Lưu Phân công
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Assignments;