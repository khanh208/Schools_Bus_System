import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaUserGraduate, FaPlus, FaEdit, FaTrash, FaTimes, FaSearch } from 'react-icons/fa';

const Students = () => {
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    // Data cho dropdown
    const [classes, setClasses] = useState([]);
    const [areas, setAreas] = useState([]);
    const [parents, setParents] = useState([]);

    const initialForm = {
        student_code: '',
        full_name: '',
        date_of_birth: '',
        gender: 'male',
        address: '',
        class_obj: '', // ID lớp
        area: '',      // ID khu vực
        parent: '',    // ID phụ huynh
        pickup_lat: 10.762622, // Mặc định HCM
        pickup_lng: 106.660172,
        dropoff_lat: 10.762622,
        dropoff_lng: 106.660172
    };
    const [formData, setFormData] = useState(initialForm);

    // 1. Tải dữ liệu
    const fetchData = async () => {
        try {
            const [resStudents, resClasses, resAreas, resParents] = await Promise.all([
                api.get('/students/students/'),
                api.get('/students/classes/'),
                api.get('/students/areas/'),
                api.get('/auth/parents/')
            ]);
            
            setStudents(resStudents.data.results || resStudents.data);
            setClasses(resClasses.data.results || resClasses.data);
            setAreas(resAreas.data.results || resAreas.data);
            setParents(resParents.data.results || resParents.data);
        } catch (error) {
            console.error("Lỗi tải dữ liệu:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    // 2. Xử lý Submit
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingId) {
                await api.patch(`/students/students/${editingId}/`, formData);
                alert("Cập nhật thành công!");
            } else {
                await api.post('/students/students/', formData);
                alert("Thêm học sinh thành công!");
            }
            setShowModal(false);
            fetchData(); // Reload list
        } catch (error) {
            alert("Lỗi: " + JSON.stringify(error.response?.data || error.message));
        }
    };

    // 3. Xử lý Delete
    const handleDelete = async (id) => {
        if (window.confirm("Bạn có chắc muốn xóa học sinh này?")) {
            await api.delete(`/students/students/${id}/`);
            fetchData();
        }
    };

    // 4. Mở Modal
    const openModal = (student = null) => {
        if (student) {
            setFormData({
                ...student,
                class_obj: student.class_obj || '',
                area: student.area || '',
                parent: student.parent || '',
                // Nếu API trả về coordinates riêng thì map vào đây
                pickup_lat: student.pickup_coordinates?.[1] || 10.762,
                pickup_lng: student.pickup_coordinates?.[0] || 106.660,
                dropoff_lat: student.dropoff_coordinates?.[1] || 10.762,
                dropoff_lng: student.dropoff_coordinates?.[0] || 106.660,
            });
            setEditingId(student.id);
        } else {
            setFormData(initialForm);
            setEditingId(null);
        }
        setShowModal(true);
    };

    // Filter
    const filteredStudents = students.filter(s => 
        s.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.student_code.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <FaUserGraduate className="text-blue-600"/> Quản lý Học sinh
                </h2>
                <div className="flex gap-2 w-full md:w-auto">
                    <div className="relative flex-1">
                        <FaSearch className="absolute left-3 top-3 text-gray-400"/>
                        <input 
                            className="pl-10 pr-4 py-2 border rounded-lg w-full focus:ring-2 focus:ring-blue-500 outline-none"
                            placeholder="Tìm tên, mã HS..."
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <button onClick={() => openModal()} className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2 whitespace-nowrap">
                        <FaPlus /> Thêm mới
                    </button>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 text-sm text-gray-600 uppercase">
                        <tr>
                            <th className="p-3">Mã HS</th>
                            <th className="p-3">Họ tên</th>
                            <th className="p-3">Lớp</th>
                            <th className="p-3">Khu vực</th>
                            <th className="p-3">Phụ huynh</th>
                            <th className="p-3 text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 text-sm">
                        {filteredStudents.map(s => (
                            <tr key={s.id} className="hover:bg-gray-50">
                                <td className="p-3 font-mono text-blue-600">{s.student_code}</td>
                                <td className="p-3 font-bold text-gray-700">{s.full_name}</td>
                                <td className="p-3">{s.class_name || '-'}</td>
                                <td className="p-3">{s.area_name || '-'}</td>
                                <td className="p-3">{s.parent_name || '-'}</td>
                                <td className="p-3 text-right flex justify-end gap-2">
                                    <button onClick={() => openModal(s)} className="text-blue-600 hover:bg-blue-50 p-2 rounded"><FaEdit/></button>
                                    <button onClick={() => handleDelete(s.id)} className="text-red-600 hover:bg-red-50 p-2 rounded"><FaTrash/></button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Modal Form */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[1200] p-4">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                        <div className="p-4 border-b flex justify-between items-center sticky top-0 bg-white z-10">
                            <h3 className="font-bold text-lg">{editingId ? 'Sửa thông tin' : 'Thêm học sinh mới'}</h3>
                            <button onClick={() => setShowModal(false)}><FaTimes size={20}/></button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Basic Info */}
                            <div className="col-span-2"><h4 className="font-bold text-gray-500 border-b pb-1 mb-2">Thông tin cơ bản</h4></div>
                            
                            <input placeholder="Mã HS (Tự động nếu để trống)" className="border p-2 rounded" 
                                value={formData.student_code} onChange={e => setFormData({...formData, student_code: e.target.value})} />
                            
                            <input placeholder="Họ và tên (*)" required className="border p-2 rounded" 
                                value={formData.full_name} onChange={e => setFormData({...formData, full_name: e.target.value})} />
                            
                            <input type="date" required className="border p-2 rounded" title="Ngày sinh"
                                value={formData.date_of_birth} onChange={e => setFormData({...formData, date_of_birth: e.target.value})} />

                            <select className="border p-2 rounded" value={formData.gender} onChange={e => setFormData({...formData, gender: e.target.value})}>
                                <option value="male">Nam</option>
                                <option value="female">Nữ</option>
                            </select>

                            {/* Relations */}
                            <div className="col-span-2 mt-2"><h4 className="font-bold text-gray-500 border-b pb-1 mb-2">Phân công</h4></div>

                            <select className="border p-2 rounded" value={formData.class_obj} onChange={e => setFormData({...formData, class_obj: e.target.value})}>
                                <option value="">-- Chọn Lớp --</option>
                                {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                            </select>

                            <select className="border p-2 rounded" value={formData.area} onChange={e => setFormData({...formData, area: e.target.value})}>
                                <option value="">-- Chọn Khu vực --</option>
                                {areas.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                            </select>

                            <select className="border p-2 rounded col-span-2" value={formData.parent} onChange={e => setFormData({...formData, parent: e.target.value})}>
                                <option value="">-- Chọn Phụ huynh --</option>
                                {parents.map(p => <option key={p.id} value={p.id}>{p.user.full_name} ({p.user.phone})</option>)}
                            </select>

                            {/* Location (Simplified for demo) */}
                            <div className="col-span-2 mt-2"><h4 className="font-bold text-gray-500 border-b pb-1 mb-2">Địa chỉ & Vị trí</h4></div>
                            <input placeholder="Địa chỉ nhà" className="border p-2 rounded col-span-2" required
                                value={formData.address} onChange={e => setFormData({...formData, address: e.target.value})} />
                            
                            {/* Hidden Lat/Lng inputs or Map picker would go here */}
                            
                            <div className="col-span-2 mt-4 flex justify-end gap-3">
                                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">Hủy</button>
                                <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-bold">Lưu lại</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Students;