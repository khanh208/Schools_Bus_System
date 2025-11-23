import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaTimes, FaCheck, FaSignOutAlt, FaUserSlash, FaUserGraduate } from 'react-icons/fa';

const AttendanceModal = ({ trip, onClose }) => {
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [attendanceData, setAttendanceData] = useState({}); // Lưu trạng thái điểm danh cục bộ

    // 1. Lấy danh sách học sinh của tuyến này
    useEffect(() => {
        const fetchStudents = async () => {
            try {
                // SỬA LỖI: Dùng trip.route (là ID) thay vì trip.route.id
                const routeId = typeof trip.route === 'object' ? trip.route.id : trip.route;
                
                // Gọi API lấy học sinh gán cho tuyến
                const resStudents = await api.get(`/routes/routes/${routeId}/students/`);
                
                // Sắp xếp học sinh theo thứ tự điểm dừng
                const sortedList = resStudents.data.sort((a, b) => a.stop - b.stop);
                setStudents(sortedList);
            } catch (error) {
                console.error("Lỗi tải DS học sinh:", error);
            } finally {
                setLoading(false);
            }
        };
        
        if (trip) fetchStudents();
    }, [trip]);

    // 2. Xử lý điểm danh
    const handleAttendance = async (student, type, status) => {
        try {
            // Gọi API điểm danh
            await api.post('/attendance/records/check_in/', {
                trip: trip.id,
                student: student.student, // ID học sinh
                stop: student.stop,       // ID điểm dừng
                attendance_type: type,    // 'check_in' hoặc 'check_out'
                status: status,           // 'present', 'absent'
                lat: 0, 
                lng: 0
            });

            // Cập nhật UI ngay lập tức
            setAttendanceData(prev => ({
                ...prev,
                [student.student]: { type, status }
            }));

        } catch (error) {
            alert("Lỗi điểm danh: " + JSON.stringify(error.response?.data || error.message));
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 z-[1300] flex items-end sm:items-center justify-center animate-[fadeIn_0.2s]">
            <div className="bg-white w-full max-w-lg rounded-t-2xl sm:rounded-2xl h-[85vh] flex flex-col overflow-hidden shadow-2xl">
                
                {/* Header */}
                <div className="p-4 border-b flex justify-between items-center bg-blue-600 text-white shadow-md">
                    <div>
                        <h3 className="font-bold text-lg flex items-center gap-2">
                            <FaUserGraduate /> Điểm danh Học sinh
                        </h3>
                        <p className="text-xs text-blue-100 opacity-90">
                            Chuyến: {trip?.route_info?.name || trip?.route_name}
                        </p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-blue-700 rounded-full transition-colors">
                        <FaTimes size={20} />
                    </button>
                </div>

                {/* List */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-40 text-gray-500">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
                            <p>Đang tải danh sách...</p>
                        </div>
                    ) : students.length === 0 ? (
                        <div className="text-center py-10 px-4">
                            <p className="text-gray-500 mb-2">Chưa có học sinh nào đăng ký tuyến này.</p>
                            <p className="text-xs text-gray-400">Vui lòng kiểm tra lại cấu hình Tuyến đường trong Admin.</p>
                        </div>
                    ) : (
                        students.map((item) => {
                            const status = attendanceData[item.student];
                            return (
                                <div key={item.id} className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                                    <div className="flex justify-between items-start mb-3">
                                        <div>
                                            <h4 className="font-bold text-gray-800 text-lg">{item.student_name}</h4>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600 font-mono">{item.student_code}</span>
                                            </div>
                                            <p className="text-xs text-blue-600 mt-1 font-medium">
                                                📍 Điểm: {item.stop_name}
                                            </p>
                                        </div>
                                        
                                        {/* Trạng thái đã điểm danh */}
                                        {status && (
                                            <span className={`px-3 py-1 rounded-full text-xs font-bold shadow-sm ${
                                                status.status === 'absent' ? 'bg-red-100 text-red-700 border border-red-200' : 
                                                status.type === 'check_in' ? 'bg-green-100 text-green-700 border border-green-200' : 
                                                'bg-gray-100 text-gray-700 border border-gray-200'
                                            }`}>
                                                {status.status === 'absent' ? 'Vắng' : (status.type === 'check_in' ? 'Đã lên xe' : 'Đã xuống xe')}
                                            </span>
                                        )}
                                    </div>

                                    {/* Actions Buttons */}
                                    <div className="grid grid-cols-3 gap-3 mt-2">
                                        <button 
                                            onClick={() => handleAttendance(item, 'check_in', 'present')}
                                            className={`flex flex-col items-center justify-center p-2 rounded-lg border transition-all active:scale-95 ${
                                                status?.type === 'check_in' 
                                                ? 'bg-green-600 text-white border-green-600 shadow-md' 
                                                : 'bg-white text-green-600 border-green-200 hover:bg-green-50'
                                            }`}
                                        >
                                            <FaCheck size={16} className="mb-1" />
                                            <span className="text-xs font-bold">Lên xe</span>
                                        </button>

                                        <button 
                                            onClick={() => handleAttendance(item, 'check_out', 'present')}
                                            className={`flex flex-col items-center justify-center p-2 rounded-lg border transition-all active:scale-95 ${
                                                status?.type === 'check_out'
                                                ? 'bg-gray-600 text-white border-gray-600 shadow-md'
                                                : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                                            }`}
                                        >
                                            <FaSignOutAlt size={16} className="mb-1" />
                                            <span className="text-xs font-bold">Xuống xe</span>
                                        </button>

                                        <button 
                                            onClick={() => handleAttendance(item, 'check_in', 'absent')}
                                            className={`flex flex-col items-center justify-center p-2 rounded-lg border transition-all active:scale-95 ${
                                                status?.status === 'absent'
                                                ? 'bg-red-500 text-white border-red-500 shadow-md'
                                                : 'bg-white text-red-500 border-red-200 hover:bg-red-50'
                                            }`}
                                        >
                                            <FaUserSlash size={16} className="mb-1" />
                                            <span className="text-xs font-bold">Vắng</span>
                                        </button>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>
        </div>
    );
};

export default AttendanceModal;