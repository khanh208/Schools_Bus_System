import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaClipboardList, FaSearch, FaCheck, FaTimes, FaClock } from 'react-icons/fa';

const Attendance = () => {
    const [records, setRecords] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterDate, setFilterDate] = useState(new Date().toISOString().split('T')[0]);
    
    const fetchRecords = async () => {
        setLoading(true);
        try {
            // Gọi API lọc theo ngày (Backend cần hỗ trợ filter này)
            const res = await api.get(`/attendance/records/?from_date=${filterDate}&to_date=${filterDate}`);
            setRecords(res.data.results || res.data);
        } catch (error) {
            console.error("Lỗi tải điểm danh:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRecords();
    }, [filterDate]);

    const getStatusBadge = (status) => {
        switch(status) {
            case 'present': return <span className="px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-bold">Có mặt</span>;
            case 'absent': return <span className="px-2 py-1 rounded-full bg-red-100 text-red-700 text-xs font-bold">Vắng</span>;
            case 'late': return <span className="px-2 py-1 rounded-full bg-yellow-100 text-yellow-700 text-xs font-bold">Muộn</span>;
            default: return status;
        }
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <FaClipboardList className="text-blue-600"/> Nhật ký Điểm danh
                </h2>
                
                <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-600">Ngày:</label>
                    <input 
                        type="date" 
                        className="border p-2 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                        value={filterDate}
                        onChange={e => setFilterDate(e.target.value)}
                    />
                    <button onClick={fetchRecords} className="bg-gray-100 p-2 rounded hover:bg-gray-200">
                        <FaSearch />
                    </button>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 text-xs uppercase text-gray-600">
                        <tr>
                            <th className="p-3">Thời gian</th>
                            <th className="p-3">Học sinh</th>
                            <th className="p-3">Mã HS</th>
                            <th className="p-3">Chuyến / Tuyến</th>
                            <th className="p-3">Loại</th>
                            <th className="p-3 text-center">Trạng thái</th>
                            <th className="p-3">Người check</th>
                        </tr>
                    </thead>
                    <tbody className="text-sm divide-y divide-gray-100">
                        {loading ? (
                            <tr><td colSpan="7" className="text-center py-8">Đang tải dữ liệu...</td></tr>
                        ) : records.length === 0 ? (
                            <tr><td colSpan="7" className="text-center py-8 text-gray-500">Không có dữ liệu điểm danh ngày này.</td></tr>
                        ) : records.map(record => (
                            <tr key={record.id} className="hover:bg-gray-50">
                                <td className="p-3 font-mono text-gray-600">
                                    {new Date(record.check_time).toLocaleTimeString('vi-VN', {hour: '2-digit', minute:'2-digit'})}
                                </td>
                                <td className="p-3 font-bold text-gray-800">{record.student_name}</td>
                                <td className="p-3 text-xs text-gray-500">{record.student_code}</td>
                                <td className="p-3">
                                    <div className="text-xs text-blue-600 font-bold">Trip #{record.trip}</div>
                                </td>
                                <td className="p-3">
                                    {record.attendance_type === 'check_in' ? 
                                        <span className="text-green-600 flex items-center gap-1"><FaCheck size={10}/> Lên xe</span> : 
                                        <span className="text-orange-600 flex items-center gap-1"><FaSignOutAlt size={10}/> Xuống xe</span>
                                    }
                                </td>
                                <td className="p-3 text-center">
                                    {getStatusBadge(record.status)}
                                </td>
                                <td className="p-3 text-xs text-gray-500">
                                    {record.checked_by_name || 'System'}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
// Icon fix
import { FaSignOutAlt } from 'react-icons/fa';

export default Attendance;