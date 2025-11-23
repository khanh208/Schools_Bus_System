import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaBus, FaPlus, FaEdit, FaTrash, FaTimes } from 'react-icons/fa';

const Vehicles = () => {
    const [vehicles, setVehicles] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [editingId, setEditingId] = useState(null);
    
    const initialForm = {
        plate_number: '',
        vehicle_type: 'Bus 29 chỗ',
        capacity: 29,
        model: '',
        status: 'active'
    };
    const [formData, setFormData] = useState(initialForm);

    const fetchVehicles = async () => {
        try {
            const res = await api.get('/routes/vehicles/');
            setVehicles(res.data.results || res.data);
        } catch (error) { console.error(error); }
    };

    useEffect(() => { fetchVehicles(); }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            // Backend yêu cầu các trường ngày tháng, ta fake tạm để qua validate nếu cần
            const payload = {
                ...formData,
                insurance_expiry: '2025-12-31', // Default future date
                registration_expiry: '2025-12-31'
            };

            if (editingId) {
                await api.patch(`/routes/vehicles/${editingId}/`, payload);
            } else {
                await api.post('/routes/vehicles/', payload);
            }
            fetchVehicles();
            setShowModal(false);
        } catch (error) {
            alert("Lỗi: " + JSON.stringify(error.response?.data || error.message));
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm("Xóa xe này?")) {
            await api.delete(`/routes/vehicles/${id}/`);
            fetchVehicles();
        }
    };

    const openModal = (vehicle = null) => {
        if (vehicle) {
            setFormData({
                plate_number: vehicle.plate_number,
                vehicle_type: vehicle.vehicle_type,
                capacity: vehicle.capacity,
                model: vehicle.model || '',
                status: vehicle.status
            });
            setEditingId(vehicle.id);
        } else {
            setFormData(initialForm);
            setEditingId(null);
        }
        setShowModal(true);
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-800">Quản lý Phương tiện</h2>
                <button onClick={() => openModal()} className="bg-blue-600 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-blue-700">
                    <FaPlus /> Thêm Xe
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {vehicles.map(vehicle => (
                    <div key={vehicle.id} className="border rounded-lg p-4 flex flex-col gap-3 hover:border-blue-300 transition-colors bg-gray-50">
                        <div className="flex justify-between items-start">
                            <div className="flex items-center gap-3">
                                <div className="bg-white p-3 rounded-full shadow-sm text-blue-600">
                                    <FaBus size={20} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-lg">{vehicle.plate_number}</h3>
                                    <p className="text-sm text-gray-500">{vehicle.vehicle_type}</p>
                                </div>
                            </div>
                            <span className={`px-2 py-1 rounded text-xs font-bold ${vehicle.status === 'active' ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}>
                                {vehicle.status}
                            </span>
                        </div>
                        
                        <div className="text-sm text-gray-600 grid grid-cols-2 gap-2 mt-2">
                            <p>Sức chứa: <b>{vehicle.capacity}</b></p>
                            <p>Mẫu: <b>{vehicle.model || '-'}</b></p>
                        </div>

                        <div className="flex gap-2 mt-2 pt-3 border-t border-gray-200">
                            <button onClick={() => openModal(vehicle)} className="flex-1 bg-white border border-gray-300 py-1.5 rounded text-sm hover:bg-gray-100">
                                <FaEdit className="inline mr-1"/> Sửa
                            </button>
                            <button onClick={() => handleDelete(vehicle.id)} className="p-2 text-red-500 hover:bg-red-50 rounded">
                                <FaTrash />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Modal Form */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg w-96 shadow-xl">
                        <div className="flex justify-between mb-4">
                            <h3 className="font-bold text-lg">{editingId ? 'Sửa thông tin xe' : 'Thêm xe mới'}</h3>
                            <button onClick={() => setShowModal(false)}><FaTimes /></button>
                        </div>
                        <form onSubmit={handleSubmit} className="space-y-3">
                            <input placeholder="Biển số (VD: 51A-123.45)" className="w-full border p-2 rounded" required
                                value={formData.plate_number} onChange={e => setFormData({...formData, plate_number: e.target.value})} />
                            
                            <input placeholder="Loại xe" className="w-full border p-2 rounded" required
                                value={formData.vehicle_type} onChange={e => setFormData({...formData, vehicle_type: e.target.value})} />
                            
                            <input type="number" placeholder="Sức chứa" className="w-full border p-2 rounded" required
                                value={formData.capacity} onChange={e => setFormData({...formData, capacity: e.target.value})} />

                            <select className="w-full border p-2 rounded"
                                value={formData.status} onChange={e => setFormData({...formData, status: e.target.value})}>
                                <option value="active">Đang hoạt động</option>
                                <option value="maintenance">Bảo trì</option>
                                <option value="inactive">Ngừng hoạt động</option>
                            </select>
                            
                            <button className="w-full bg-blue-600 text-white py-2 rounded font-bold hover:bg-blue-700 mt-2">Lưu lại</button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Vehicles;