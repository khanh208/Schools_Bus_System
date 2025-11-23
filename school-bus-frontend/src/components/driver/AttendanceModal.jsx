// school-bus-frontend/src/components/driver/AttendanceModal.jsx

import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaTimes, FaCheck, FaSignOutAlt, FaUserSlash, FaUserGraduate, FaSpinner } from 'react-icons/fa';

const AttendanceModal = ({ trip, onClose }) => {
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [attendanceData, setAttendanceData] = useState({});
    const [processingStudentId, setProcessingStudentId] = useState(null);

    // 1. Lấy danh sách học sinh của tuyến
    useEffect(() => {
        const fetchStudents = async () => {
            try {
                // Lấy ID tuyến từ trip
                const routeId = typeof trip.route === 'object' ? trip.route.id : trip.route;
                
                if (!routeId) {
                    console.error("❌ Không tìm thấy route ID");
                    setLoading(false);
                    return;
                }

                console.log("🔍 Fetching students for route:", routeId);

                // Gọi API lấy học sinh
                const response = await api.get(`/routes/routes/${routeId}/students/`);
                
                console.log("✅ Students data:", response.data);

                // Sắp xếp theo thứ tự điểm dừng
                const sortedStudents = response.data.sort((a, b) => {
                    const orderA = a.stop?.stop_order || 999;
                    const orderB = b.stop?.stop_order || 999;
                    return orderA - orderB;
                });

                setStudents(sortedStudents);

                // Tải trạng thái điểm danh hiện có (nếu có)
                await fetchExistingAttendance(trip.id);

            } catch (error) {
                console.error("❌ Lỗi tải danh sách học sinh:", error);
                alert("Không thể tải danh sách học sinh. Vui lòng thử lại.");
            } finally {
                setLoading(false);
            }
        };

        if (trip) {
            fetchStudents();
        }
    }, [trip]);

    // 2. Lấy trạng thái điểm danh đã có
    const fetchExistingAttendance = async (tripId) => {
        try {
            const response = await api.get(`/attendance/records/?trip=${tripId}`);
            
            // Map dữ liệu thành object để dễ tra cứu
            const attendanceMap = {};
            response.data.forEach(record => {
                attendanceMap[record.student] = {
                    type: record.attendance_type,
                    status: record.status,
                    id: record.id
                };
            });

            setAttendanceData(attendanceMap);
            console.log("✅ Loaded existing attendance:", attendanceMap);
        } catch (error) {
            console.warn("⚠️ Không tải được dữ liệu điểm danh cũ:", error);
        }
    };

    // 3. Xử lý điểm danh
    const handleAttendance = async (student, type, status) => {
        const studentId = student.student;
        
        // Prevent double-click
        if (processingStudentId === studentId) {
            return;
        }

        setProcessingStudentId(studentId);

        try {
            console.log("📝 Điểm danh:", {
                student: student.student_name,
                type,
                status
            });

            // Payload gửi lên API
            const payload = {
                trip: trip.id,
                student: studentId,
                stop: student.stop,
                attendance_type: type,
                status: status,
                notes: ''
            };

            console.log("📤 Sending:", payload);

            // Gọi API điểm danh
            const response = await api.post('/attendance/records/check_in/', payload);

            console.log("✅ Điểm danh thành công:", response.data);

            // Cập nhật UI ngay lập tức
            setAttendanceData(prev => ({
                ...prev,
                [studentId]: { 
                    type, 
                    status, 
                    id: response.data.id 
                }
            }));

            // Hiển thị thông báo ngắn
            showToast(`✓ ${student.student_name} đã được điểm danh`);

        } catch (error) {
            console.error("❌ Lỗi điểm danh:", error);
            
            const errorMsg = error.response?.data?.student?.[0] 
                || error.response?.data?.detail 
                || error.response?.data?.error
                || "Lỗi không xác định";

            alert(`Điểm danh thất bại: ${errorMsg}`);
        } finally {
            setProcessingStudentId(null);
        }
    };

    // Helper: Toast notification
    const showToast = (message) => {
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.className = 'fixed top-20 right-4 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg z-[9999] animate-[fadeIn_0.3s]';
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 2000);
    };

    // 4. Render trạng thái điểm danh
    const getStatusInfo = (studentId) => {
        const status = attendanceData[studentId];
        if (!status) return null;

        if (status.status === 'absent') {
            return {
                label: 'Vắng',
                className: 'bg-red-100 text-red-700 border-red-200'
            };
        } else if (status.type === 'check_in') {
            return {
                label: 'Đã lên xe',
                className: 'bg-green-100 text-green-700 border-green-200'
            };
        } else if (status.type === 'check_out') {
            return {
                label: 'Đã xuống xe',
                className: 'bg-gray-100 text-gray-700 border-gray-200'
            };
        }
        return null;
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
                            Chuyến: {trip.route_name || 'Đang tải...'}
                        </p>
                    </div>
                    <button 
                        onClick={onClose} 
                        className="p-2 hover:bg-blue-700 rounded-full transition-colors"
                    >
                        <FaTimes size={20} />
                    </button>
                </div>

                {/* Student List */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-40 text-gray-500">
                            <FaSpinner className="animate-spin text-4xl mb-2 text-blue-600" />
                            <p>Đang tải danh sách...</p>
                        </div>
                    ) : students.length === 0 ? (
                        <div className="text-center py-10 px-4">
                            <p className="text-gray-500 mb-2">Chưa có học sinh nào đăng ký tuyến này.</p>
                            <p className="text-xs text-gray-400">Vui lòng kiểm tra lại cấu hình Tuyến đường.</p>
                        </div>
                    ) : (
                        students.map((student) => {
                            const studentId = student.student;
                            const statusInfo = getStatusInfo(studentId);
                            const isProcessing = processingStudentId === studentId;

                            return (
                                <div 
                                    key={student.id} 
                                    className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
                                >
                                    <div className="flex justify-between items-start mb-3">
                                        <div>
                                            <h4 className="font-bold text-gray-800 text-lg">
                                                {student.student_name}
                                            </h4>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600 font-mono">
                                                    {student.student_code}
                                                </span>
                                            </div>
                                            <p className="text-xs text-blue-600 mt-1 font-medium">
                                                📍 {student.stop_name || 'Điểm dừng chưa xác định'}
                                            </p>
                                        </div>
                                        
                                        {/* Status Badge */}
                                        {statusInfo && (
                                            <span className={`px-3 py-1 rounded-full text-xs font-bold shadow-sm border ${statusInfo.className}`}>
                                                {statusInfo.label}
                                            </span>
                                        )}
                                    </div>

                                    {/* Action Buttons */}
                                    <div className="grid grid-cols-3 gap-3 mt-2">
                                        <button 
                                            onClick={() => handleAttendance(student, 'check_in', 'present')}
                                            disabled={isProcessing}
                                            className={`flex flex-col items-center justify-center p-2 rounded-lg border transition-all active:scale-95 ${
                                                statusInfo?.label === 'Đã lên xe'
                                                ? 'bg-green-600 text-white border-green-600 shadow-md' 
                                                : 'bg-white text-green-600 border-green-200 hover:bg-green-50'
                                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                                        >
                                            {isProcessing ? (
                                                <FaSpinner className="animate-spin mb-1" size={16} />
                                            ) : (
                                                <FaCheck size={16} className="mb-1" />
                                            )}
                                            <span className="text-xs font-bold">Lên xe</span>
                                        </button>

                                        <button 
                                            onClick={() => handleAttendance(student, 'check_out', 'present')}
                                            disabled={isProcessing}
                                            className={`flex flex-col items-center justify-center p-2 rounded-lg border transition-all active:scale-95 ${
                                                statusInfo?.label === 'Đã xuống xe'
                                                ? 'bg-gray-600 text-white border-gray-600 shadow-md'
                                                : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                                        >
                                            {isProcessing ? (
                                                <FaSpinner className="animate-spin mb-1" size={16} />
                                            ) : (
                                                <FaSignOutAlt size={16} className="mb-1" />
                                            )}
                                            <span className="text-xs font-bold">Xuống xe</span>
                                        </button>

                                        <button 
                                            onClick={() => handleAttendance(student, 'check_in', 'absent')}
                                            disabled={isProcessing}
                                            className={`flex flex-col items-center justify-center p-2 rounded-lg border transition-all active:scale-95 ${
                                                statusInfo?.label === 'Vắng'
                                                ? 'bg-red-500 text-white border-red-500 shadow-md'
                                                : 'bg-white text-red-500 border-red-200 hover:bg-red-50'
                                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                                        >
                                            {isProcessing ? (
                                                <FaSpinner className="animate-spin mb-1" size={16} />
                                            ) : (
                                                <FaUserSlash size={16} className="mb-1" />
                                            )}
                                            <span className="text-xs font-bold">Vắng</span>
                                        </button>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>

                {/* Footer Summary */}
                <div className="p-4 border-t bg-white">
                    <div className="flex justify-between text-sm text-gray-600">
                        <span>Tổng: {students.length} HS</span>
                        <span>Đã điểm danh: {Object.keys(attendanceData).length}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AttendanceModal;