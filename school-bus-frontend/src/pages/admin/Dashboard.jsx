import React from 'react';

const Dashboard = () => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
                <h3 className="text-gray-500 text-sm font-medium uppercase">Tổng số học sinh</h3>
                <p className="text-3xl font-bold text-gray-800 mt-2">1,250</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
                <h3 className="text-gray-500 text-sm font-medium uppercase">Xe đang chạy</h3>
                <p className="text-3xl font-bold text-gray-800 mt-2">24</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
                <h3 className="text-gray-500 text-sm font-medium uppercase">Tài xế</h3>
                <p className="text-3xl font-bold text-gray-800 mt-2">45</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
                <h3 className="text-gray-500 text-sm font-medium uppercase">Cảnh báo</h3>
                <p className="text-3xl font-bold text-gray-800 mt-2">3</p>
            </div>

            {/* Placeholder cho biểu đồ hoặc bản đồ sau này */}
            <div className="col-span-1 md:col-span-4 bg-white rounded-lg shadow h-96 flex items-center justify-center text-gray-400 border-2 border-dashed">
                Khu vực hiển thị Bản đồ giám sát thời gian thực
            </div>
        </div>
    );
};

export default Dashboard;