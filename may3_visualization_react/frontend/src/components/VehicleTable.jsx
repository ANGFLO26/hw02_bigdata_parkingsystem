import { useMemo } from 'react'
import './VehicleTable.css'

function VehicleTable({ parkingLotMap }) {
  const vehicles = useMemo(() => {
    return Object.entries(parkingLotMap)
      .filter(([_, info]) => info.status === 'PARKED')
      .map(([location, info]) => ({
        location,
        ...info
      }))
      .sort((a, b) => a.location.localeCompare(b.location))
  }, [parkingLotMap])

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('vi-VN').format(amount)
  }

  const formatDuration = (minutes) => {
    if (minutes < 60) {
      return `${Math.round(minutes)} phút`
    }
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    return `${hours}h ${mins} phút`
  }

  if (vehicles.length === 0) {
    return (
      <div className="vehicle-table-empty">
        <p>Chưa có xe nào đang đỗ</p>
      </div>
    )
  }

  return (
    <div className="vehicle-table">
      <table>
        <thead>
          <tr>
            <th>Vị trí</th>
            <th>Biển số</th>
            <th>Thời gian đỗ</th>
            <th>Số block</th>
            <th>Tiền (VNĐ)</th>
          </tr>
        </thead>
        <tbody>
          {vehicles.map((vehicle) => (
            <tr key={vehicle.location}>
              <td className="location-cell">{vehicle.location}</td>
              <td className="license-cell">{vehicle.license_plate || 'N/A'}</td>
              <td className="duration-cell">
                {formatDuration(vehicle.parked_duration_minutes || 0)}
              </td>
              <td className="blocks-cell">{vehicle.parked_blocks || 0}</td>
              <td className="cost-cell">
                {formatCurrency(vehicle.total_cost || 0)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default VehicleTable

