import './Statistics.css'

function Statistics({ statistics }) {
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('vi-VN').format(amount)
  }

  return (
    <div className="statistics">
      <div className="stat-card">
        <div className="stat-label">Tổng số chỗ</div>
        <div className="stat-value">{statistics.total_locations || 60}</div>
      </div>
      
      <div className="stat-card occupied">
        <div className="stat-label">Đã đỗ</div>
        <div className="stat-value">{statistics.occupied_count || 0}</div>
      </div>
      
      <div className="stat-card available">
        <div className="stat-label">Trống</div>
        <div className="stat-value">{statistics.available_count || 60}</div>
      </div>
      
      <div className="stat-card revenue">
        <div className="stat-label">Doanh thu</div>
        <div className="stat-value">{formatCurrency(statistics.total_revenue || 0)} VNĐ</div>
      </div>
      
      <div className="stat-card messages">
        <div className="stat-label">Messages đã xử lý</div>
        <div className="stat-value">{statistics.messages_processed || 0}</div>
      </div>
    </div>
  )
}

export default Statistics

