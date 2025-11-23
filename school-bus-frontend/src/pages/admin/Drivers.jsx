import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaUserTie, FaIdCard, FaPhone, FaStar, FaBus, FaEdit, FaTimes, FaPlus, FaTrash } from 'react-icons/fa';

const Drivers = () => {
    const [drivers, setDrivers] = useState([]);
    const [vehicles, setVehicles] = useState([]); 
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [isCreating, setIsCreating] = useState(false); // Chế độ tạo mới hay sửa
    const [editingDriver, setEditingDriver] = useState(null);
    
    // Form mặc định
    const initialForm = {
        // Phần User (Chỉ dùng khi tạo mới)
        username: '',
        password: '',
        email: '',
        full_name: '',
        phone: '',
        
        // Phần Driver (Dùng cả khi tạo và sửa)
        license_number: '',
        license_expiry: '2025-12-31', // Mặc định tạm
        experience_years: 1,
        vehicle: '',
        status: 'available'
    };
    const [formData, setFormData] = useState(initialForm);

    const fetchData = async () => {
        try {
            const [resDrivers, resVehicles] = await Promise.all([
                api.get('/auth/drivers/'),
                api.get('/routes/vehicles/')
            ]);
            setDrivers(resDrivers.data.results || resDrivers.data);
            setVehicles(resVehicles.data.results || resVehicles.data);
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
        setEditingDriver(null);
        setFormData(initialForm);
        setShowModal(true);
    };

    // Mở modal Sửa
    const handleEdit = (driver) => {
        setIsCreating(false);
        setEditingDriver(driver);
        setFormData({
            ...initialForm,
            vehicle: driver.vehicle || '',
            license_number: driver.license_number,
            experience_years: driver.experience_years,
            status: driver.status,
            // Các trường User không sửa ở đây (sửa bên trang Users nếu cần)
        });
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (isCreating) {
                // API Đăng ký (Tạo User + Driver)
                await api.post('/auth/register/', {
                    ...formData,
                    role: 'driver',
                    password_confirm: formData.password // Backend yêu cầu confirm
                });
                alert("Thêm tài xế thành công!");
            } else {
                // API Cập nhật (Chỉ sửa thông tin Driver)
                await api.patch(`/auth/drivers/${editingDriver.id}/`, {
                    vehicle: formData.vehicle || null,
                    license_number: formData.license_number,
                    experience_years: formData.experience_years,
                    status: formData.status
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
        if (window.confirm("Bạn có chắc muốn xóa tài xế này? Tài khoản đăng nhập cũng sẽ bị ảnh hưởng.")) {
            try {
                await api.delete(`/auth/drivers/${id}/`);
                fetchData();
            } catch (e) { alert("Xóa thất bại"); }
        }
    };

    const getStatusColor = (status) => {
        switch(status) {
            case 'available': return 'bg-green-100 text-green-800';
            case 'on_trip': return 'bg-blue-100 text-blue-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-800">Đội ngũ Tài xế</h2>
                <div className="flex gap-2">
                    <button onClick={fetchData} className="text-blue-600 hover:underline text-sm px-3">Làm mới</button>
                    <button onClick={handleCreate} className="bg-blue-600 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-blue-700 shadow">
                        <FaPlus /> Thêm Tài xế
                    </button>
                </div>
            </div>
            
            {loading ? (
                <div className="text-center py-8 text-gray-500">Đang tải dữ liệu...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {drivers.map((driver) => (
                        <div key={driver.id} className="border rounded-xl p-5 hover:shadow-lg transition-all bg-white flex flex-col gap-3 relative group">
                            <div className="absolute top-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button onClick={() => handleEdit(driver)} className="p-2 text-blue-600 hover:bg-blue-50 rounded-full" title="Sửa">
                                    <FaEdit />
                                </button>
                                <button onClick={() => handleDelete(driver.id)} className="p-2 text-red-600 hover:bg-red-50 rounded-full" title="Xóa">
                                    <FaTrash />
                                </button>
                            </div>

                            <div className="flex items-center gap-4">
                                <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-2xl overflow-hidden">
                                    {driver.user.avatar ? <img src={driver.user.avatar} className="w-full h-full object-cover"/> : <FaUserTie />}
                                </div>
                                <div>
                                    <h3 className="font-bold text-gray-900 text-lg">{driver.user.full_name}</h3>
                                    <div className="flex items-center gap-2 text-sm mt-1">
                                        <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${getStatusColor(driver.status)}`}>
                                            {driver.status}
                                        </span>
                                        <span className="text-yellow-500 flex items-center gap-1 text-xs font-bold">
                                            <FaStar /> {driver.rating}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div className="border-t pt-3 space-y-2 text-sm text-gray-600">
                                <div className="flex justify-between">
                                    <span className="flex items-center gap-2"><FaIdCard className="text-gray-400"/> GPLX:</span>
                                    <span className="font-mono font-bold">{driver.license_number}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="flex items-center gap-2"><FaPhone className="text-gray-400"/> SĐT:</span>
                                    <span>{driver.user.phone}</span>
                                </div>
                                
                                <div className={`mt-2 p-2 rounded border flex items-center gap-3 ${driver.vehicle_info ? 'bg-blue-50 border-blue-100' : 'bg-gray-50 border-dashed'}`}>
                                    <FaBus className={driver.vehicle_info ? "text-blue-600" : "text-gray-400"} />
                                    <div>
                                        <p className="text-xs text-gray-500">Phương tiện phụ trách</p>
                                        <p className="font-bold text-gray-800">
                                            {driver.vehicle_info 
                                                ? `${driver.vehicle_info.plate_number} (${driver.vehicle_info.vehicle_type})` 
                                                : 'Chưa gán xe'}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* MODAL FORM */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[1100] p-4">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-[fadeIn_0.2s] overflow-hidden">
                        <div className="p-4 border-b flex justify-between items-center bg-gray-50">
                            <h3 className="font-bold text-lg text-gray-800">{isCreating ? 'Thêm Tài xế Mới' : 'Cập nhật Tài xế'}</h3>
                            <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600"><FaTimes size={20}/></button>
                        </div>
                        
                        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
                            
                            {/* Phần tạo User mới (Chỉ hiện khi Creating) */}
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

                            {/* Phần thông tin nghề nghiệp */}
                            <p className="text-xs font-bold text-green-600 uppercase tracking-wide">Thông tin nghề nghiệp</p>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm text-gray-600 mb-1">Số GPLX (*)</label>
                                    <input className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none" required
                                        value={formData.license_number} onChange={e => setFormData({...formData, license_number: e.target.value})} />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-600 mb-1">Kinh nghiệm (năm)</label>
                                    <input type="number" className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                                        value={formData.experience_years} onChange={e => setFormData({...formData, experience_years: e.target.value})} />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm text-gray-600 mb-1">Gán xe phụ trách</label>
                                <select className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={formData.vehicle} onChange={e => setFormData({...formData, vehicle: e.target.value})}>
                                    <option value="">-- Chưa gán xe --</option>
                                    {vehicles.map(v => (
                                        <option key={v.id} value={v.id}>{v.plate_number} - {v.model} ({v.capacity} chỗ)</option>
                                    ))}
                                </select>
                            </div>

                            {!isCreating && (
                                <div>
                                    <label className="block text-sm text-gray-600 mb-1">Trạng thái</label>
                                    <select className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                                        value={formData.status} onChange={e => setFormData({...formData, status: e.target.value})}>
                                        <option value="available">Sẵn sàng</option>
                                        <option value="on_trip">Đang chạy</option>
                                        <option value="off_duty">Nghỉ việc/Nghỉ phép</option>
                                    </select>
                                </div>
                            )}

                            <button type="submit" className="w-full bg-blue-600 text-white py-3 rounded-xl font-bold hover:bg-blue-700 shadow-lg mt-4">
                                {isCreating ? 'Tạo Tài xế Mới' : 'Lưu Thay Đổi'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Drivers;