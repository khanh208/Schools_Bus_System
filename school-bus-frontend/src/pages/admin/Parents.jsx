import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaUsers, FaChild, FaPhoneAlt, FaMapMarkerAlt } from 'react-icons/fa';

const Parents = () => {
    const [parents, setParents] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await api.get('/auth/parents/');
                setParents(res.data.results || res.data);
            } catch (error) {
                console.error(error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    return (
        <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <FaUsers className="text-blue-600" /> Danh sách Phụ huynh
                </h2>
            </div>
            
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 text-gray-700 text-sm uppercase">
                        <tr>
                            <th className="px-6 py-3 font-bold">Họ tên</th>
                            <th className="px-6 py-3 font-bold">Liên hệ</th>
                            <th className="px-6 py-3 font-bold">Địa chỉ</th>
                            <th className="px-6 py-3 font-bold text-center">Số con</th>
                            <th className="px-6 py-3 font-bold">Khẩn cấp</th>
                        </tr>
                    </thead>
                    <tbody className="text-gray-600 text-sm divide-y divide-gray-100">
                        {loading ? (
                            <tr><td colSpan="5" className="text-center py-8">Đang tải...</td></tr>
                        ) : parents.map((parent) => (
                            <tr key={parent.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4">
                                    <div className="font-semibold text-gray-900">{parent.user.full_name}</div>
                                    <div className="text-xs text-gray-500">{parent.user.username}</div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <FaPhoneAlt className="text-gray-400 text-xs" />
                                        {parent.user.phone}
                                    </div>
                                    <div className="text-xs text-blue-500 mt-1">{parent.user.email}</div>
                                </td>
                                <td className="px-6 py-4 max-w-xs truncate" title={parent.address}>
                                    <div className="flex items-center gap-2">
                                        <FaMapMarkerAlt className="text-gray-400" />
                                        <span className="truncate">{parent.address}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-blue-50 text-blue-700 font-bold text-xs">
                                        <FaChild className="mr-1" /> {parent.children_count}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-red-500 font-medium">{parent.emergency_contact}</span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Parents;