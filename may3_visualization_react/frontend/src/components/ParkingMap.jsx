import { useMemo } from 'react'
import './ParkingMap.css'

function ParkingMap({ parkingLotMap }) {
  const floors = ['A', 'B', 'C', 'D', 'E', 'F']
  
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

  return (
    <div className="parking-map">
      {floors.map((floor) => (
        <div key={floor} className="floor-section">
          <h3 className="floor-title">Tầng {floor}</h3>
          <div className="parking-spots-row">
            {Array.from({ length: 10 }, (_, i) => {
              const location = `${floor}${i + 1}`
              const vehicleInfo = parkingLotMap[location]
              const isOccupied = !!vehicleInfo

              return (
                <div
                  key={location}
                  className={`parking-spot ${isOccupied ? 'occupied' : 'available'}`}
                  title={
                    isOccupied
                      ? `${vehicleInfo.license_plate} - ${formatDuration(vehicleInfo.parked_duration_minutes || 0)} - ${formatCurrency(vehicleInfo.total_cost || 0)} VNĐ`
                      : 'Trống'
                  }
                >
                  <div className="spot-location">{location}</div>
                  {isOccupied ? (
                    <>
                      <div className="spot-license">
                        {vehicleInfo.license_plate || 'N/A'}
                      </div>
                      <div className="spot-duration">
                        {formatDuration(vehicleInfo.parked_duration_minutes || 0)}
                      </div>
                      <div className="spot-cost">
                        {formatCurrency(vehicleInfo.total_cost || 0)} đ
                      </div>
                    </>
                  ) : (
                    <div className="spot-empty">TRỐNG</div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

export default ParkingMap

