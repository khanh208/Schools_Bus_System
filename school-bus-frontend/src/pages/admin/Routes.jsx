import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaPlus, FaMapMarkedAlt, FaEdit, FaTrash, FaTimes } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

const RoutesPage = () => {
    const navigate = useNavigate();
    const [routes, setRoutes] = useState([]);
    const [drivers, setDrivers] = useState([]); 
    const [vehicles, setVehicles] = useState([]); 
    
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingId, setEditingId] = useState(null);
    
    const initialForm = {
        route_code: '',
        route_name: '',
        route_type: 'pickup',
        description: '',
        driver: '',
        vehicle: ''
    };
    const [formData, setFormData] = useState(initialForm);

    const fetchData = async () => {
        try {
            const [resRoutes, resDrivers, resVehicles] = await Promise.all([
                api.get('/routes/routes/'),
                api.get('/auth/drivers/'),
                api.get('/routes/vehicles/')
            ]);

            setRoutes(resRoutes.data.results || resRoutes.data);
            setDrivers(resDrivers.data.results || resDrivers.data);
            setVehicles(resVehicles.data.results || resVehicles.data);
        } catch (error) {
            console.error("Lỗi tải dữ liệu:", error);
            // Nếu lỗi 401/403 thì đẩy về login
            if (error.response && [401, 403].includes(error.response.status)) {
                alert("Phiên đăng nhập hết hạn hoặc không có quyền. Vui lòng đăng nhập lại Admin.");
                window.location.href = '/login';
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    const handleCreate = () => {
        setFormData(initialForm);
        setEditingId(null);
        setShowModal(true);
    };

    const handleEdit = (route) => {
        setFormData({
            route_code: route.route_code,
            route_name: route.route_name,
            route_type: route.route_type,
            description: route.description || '',
            driver: route.driver || '',
            vehicle: route.vehicle || ''
        });
        setEditingId(route.id);
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            // Chuyển đổi dữ liệu an toàn trước khi gửi
            const payload = {
                ...formData,
                driver: formData.driver ? parseInt(formData.driver) : null,
                vehicle: formData.vehicle ? parseInt(formData.vehicle) : null
            };

            if (editingId) {
                await api.patch(`/routes/routes/${editingId}/`, payload);
                alert("Cập nhật thành công!");
            } else {
                await api.post('/routes/routes/', payload);
                alert("Tạo mới thành công!");
            }
            setShowModal(false);
            fetchData(); 
        } catch (error) {
            console.error(error);
            const msg = error.response?.data 
                ? JSON.stringify(error.response.data) 
                : "Lỗi kết nối server";
            alert("Lưu thất bại: " + msg);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm("Bạn có chắc muốn xóa tuyến này không?")) {
            try {
                await api.delete(`/routes/routes/${id}/`);
                fetchData();
            } catch (error) {
                alert("Xóa thất bại! (Có thể tuyến đang được sử dụng)");
            }
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-md min-h-[500px]">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-800">Quản lý Tuyến đường</h2>
                <button onClick={handleCreate} className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 shadow">
                    <FaPlus /> Thêm mới
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
                {loading ? <p>Đang tải...</p> : routes.map((route) => (
                    <div key={route.id} className="border rounded-xl p-5 hover:shadow-lg transition-all bg-white group">
                        <div className="flex justify-between items-start mb-3">
                            <div>
                                <h3 className="font-bold text-lg text-gray-800">{route.route_name}</h3>
                                <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded text-gray-600">{route.route_code}</span>
                            </div>
                            <span className={`px-2 py-1 rounded text-xs font-bold ${
                                route.route_type === 'pickup' ? 'bg-blue-100 text-blue-700' :
                                route.route_type === 'dropoff' ? 'bg-orange-100 text-orange-700' : 'bg-purple-100 text-purple-700'
                            }`}>
                                {route.route_type === 'pickup' ? 'Đón' : route.route_type === 'dropoff' ? 'Trả' : '2 Chiều'}
                            </span>
                        </div>
                        
                        <div className="text-sm text-gray-600 space-y-2 my-3 border-t border-b py-2">
                            <div className="flex justify-between">
                                <span>Tài xế:</span>
                                <span className="font-medium text-blue-600">
                                    {route.driver_info?.name || "Chưa gán"}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span>Xe:</span>
                                <span className="font-medium text-gray-800">
                                    {route.vehicle_info?.plate_number || "Chưa gán"}
                                </span>
                            </div>
                        </div>
                        
                        <div className="flex gap-2 mt-4">
                            <button 
                                onClick={() => navigate(`/admin/routes/${route.id}`)} 
                                className="flex-1 bg-gray-50 text-gray-600 py-2 rounded hover:bg-gray-100 text-sm font-medium flex items-center justify-center gap-1"
                            >
                                <FaMapMarkedAlt /> Chi tiết
                            </button>
                            <button onClick={() => handleEdit(route)} className="p-2 text-blue-600 hover:bg-blue-50 rounded">
                                <FaEdit />
                            </button>
                            <button onClick={() => handleDelete(route.id)} className="p-2 text-red-600 hover:bg-red-50 rounded">
                                <FaTrash />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
                        <div className="p-4 border-b flex justify-between items-center sticky top-0 bg-white">
                            <h3 className="font-bold text-lg">{editingId ? 'Cập nhật Tuyến' : 'Thêm Tuyến Mới'}</h3>
                            <button onClick={() => setShowModal(false)}><FaTimes /></button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Mã tuyến (*)</label>
                                    <input type="text" required className="w-full border rounded p-2"
                                        value={formData.route_code}
                                        onChange={e => setFormData({...formData, route_code: e.target.value})} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Loại</label>
                                    <select className="w-full border rounded p-2"
                                        value={formData.route_type}
                                        onChange={e => setFormData({...formData, route_type: e.target.value})}>
                                        <option value="pickup">Đón (Sáng)</option>
                                        <option value="dropoff">Trả (Chiều)</option>
                                        <option value="both">Cả hai</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Tên tuyến (*)</label>
                                <input type="text" required className="w-full border rounded p-2"
                                    value={formData.route_name}
                                    onChange={e => setFormData({...formData, route_name: e.target.value})} />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Tài xế phụ trách</label>
                                <select 
                                    className="w-full border rounded p-2 bg-white"
                                    value={formData.driver}
                                    onChange={e => setFormData({...formData, driver: e.target.value})}
                                >
                                    <option value="">-- Chưa gán --</option>
                                    {drivers.map(d => (
                                        <option key={d.id} value={d.id}>
                                            {d.user.full_name} ({d.user.phone})
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Xe vận hành</label>
                                <select 
                                    className="w-full border rounded p-2 bg-white"
                                    value={formData.vehicle}
                                    onChange={e => setFormData({...formData, vehicle: e.target.value})}
                                >
                                    <option value="">-- Chưa gán --</option>
                                    {vehicles.map(v => (
                                        <option key={v.id} value={v.id}>
                                            {v.plate_number} - {v.capacity} chỗ
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <button type="submit" className="w-full bg-blue-600 text-white py-2.5 rounded hover:bg-blue-700 font-bold shadow">
                                {editingId ? 'Lưu Cập Nhật' : 'Tạo Mới'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RoutesPage;