import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaDatabase, FaDownload, FaHistory, FaUndo, FaTrash } from 'react-icons/fa';

const Backup = () => {
    const [backups, setBackups] = useState([]);
    const [loading, setLoading] = useState(false);

    const fetchBackups = async () => {
        try {
            const res = await api.get('/backup/logs/');
            setBackups(res.data.results || res.data);
        } catch(e) { console.error(e); }
    };

    useEffect(() => { fetchBackups(); }, []);

    const handleBackup = async () => {
        setLoading(true);
        try {
            await api.post('/backup/logs/create_backup/');
            alert("Sao lưu thành công!");
            fetchBackups();
        } catch (e) { alert("Lỗi sao lưu"); }
        finally { setLoading(false); }
    };

    const handleRestore = async (id) => {
        if (window.confirm('CẢNH BÁO: Phục hồi dữ liệu sẽ ghi đè lên dữ liệu hiện tại. Bạn có chắc không?')) {
            try {
                await api.post(`/backup/logs/${id}/restore/`);
                alert('Phục hồi dữ liệu thành công!');
            } catch (e) { alert('Lỗi phục hồi'); }
        }
    };

    // --- HÀM XÓA MỚI ---
    const handleDelete = async (id) => {
        if (window.confirm('Bạn có chắc muốn xóa bản sao lưu này không? Hành động này cũng sẽ xóa file vật lý.')) {
            try {
                await api.delete(`/backup/logs/${id}/`);
                // Cập nhật lại danh sách ngay lập tức
                setBackups(prev => prev.filter(item => item.id !== id));
                alert("Đã xóa bản sao lưu.");
            } catch (e) {
                alert("Lỗi khi xóa.");
            }
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                    <FaDatabase className="text-blue-600"/> Quản lý Sao lưu
                </h2>
                <button 
                    onClick={handleBackup}
                    disabled={loading}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 flex gap-2 items-center shadow"
                >
                    {loading ? 'Đang xử lý...' : <><FaDownload/> Tạo bản sao lưu mới</>}
                </button>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="p-4 border-b font-bold text-gray-700 flex items-center gap-2 bg-gray-50">
                    <FaHistory /> Lịch sử Sao lưu
                </div>
                <table className="w-full text-left">
                    <thead className="bg-gray-100 uppercase text-xs text-gray-600 border-b">
                        <tr>
                            <th className="p-4">Thời gian</th>
                            <th className="p-4">Tên File</th>
                            <th className="p-4">Dung lượng</th>
                            <th className="p-4">Người tạo</th>
                            <th className="p-4 text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {backups.length === 0 ? (
                            <tr><td colSpan="5" className="p-8 text-center text-gray-500">Chưa có bản sao lưu nào.</td></tr>
                        ) : backups.map((log) => (
                            <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                                <td className="p-4 text-gray-700">{new Date(log.created_at).toLocaleString()}</td>
                                <td className="p-4 font-mono text-blue-600 text-sm">{log.file_name || log.backup_path}</td>
                                <td className="p-4 font-medium">{log.file_size_mb} MB</td>
                                <td className="p-4 text-gray-600">{log.performed_by_name || 'Hệ thống'}</td>
                                <td className="p-4 text-right flex justify-end gap-2">
                                    <button 
                                        onClick={() => handleRestore(log.id)}
                                        className="text-blue-600 hover:bg-blue-50 px-3 py-1.5 rounded border border-blue-200 text-sm flex items-center gap-1 transition-colors"
                                        title="Phục hồi dữ liệu này"
                                    >
                                        <FaUndo /> Phục hồi
                                    </button>
                                    
                                    {/* Nút xóa mới */}
                                    <button 
                                        onClick={() => handleDelete(log.id)}
                                        className="text-red-600 hover:bg-red-50 px-3 py-1.5 rounded border border-red-200 text-sm flex items-center gap-1 transition-colors"
                                        title="Xóa bản sao lưu này"
                                    >
                                        <FaTrash /> Xóa
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Backup;