import { useState, useEffect } from 'react'
import { io } from 'socket.io-client'
import './App.css'
import Statistics from './components/Statistics'
import ParkingMap from './components/ParkingMap'
import VehicleTable from './components/VehicleTable'

// Default config (sẽ được override từ config.json)
const DEFAULT_SOCKET_URL = 'http://localhost:5000'

function App() {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)
  const [socketUrl, setSocketUrl] = useState(DEFAULT_SOCKET_URL)
  const [configMode, setConfigMode] = useState('local')
  const [parkingLotMap, setParkingLotMap] = useState({})
  const [statistics, setStatistics] = useState({
    total_locations: 60,
    occupied_count: 0,
    available_count: 60,
    total_revenue: 0,
    messages_processed: 0
  })

  // Load config từ file
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const response = await fetch('/config.json')
        const config = await response.json()
        const url = config.frontend?.websocket_url || DEFAULT_SOCKET_URL
        setSocketUrl(url)
        setConfigMode(config.mode || 'local')
        console.log(`✅ Đã load config: mode=${config.mode}, WebSocket URL=${url}`)
      } catch (error) {
        console.warn('⚠️ Không thể load config.json, sử dụng mặc định:', error)
        setSocketUrl(DEFAULT_SOCKET_URL)
        setConfigMode('local')
      }
    }
    loadConfig()
  }, [])

  useEffect(() => {
    if (!socketUrl) return // Chờ load config xong
    
    // Kết nối WebSocket
    console.log(`🔌 Đang kết nối đến: ${socketUrl}`)
    const newSocket = io(socketUrl, {
      transports: ['websocket', 'polling']
    })

    newSocket.on('connect', () => {
      console.log('✅ Đã kết nối đến WebSocket server')
      setConnected(true)
    })

    newSocket.on('disconnect', () => {
      console.log('❌ Đã ngắt kết nối')
      setConnected(false)
    })

    newSocket.on('connected', (data) => {
      console.log('Server response:', data)
    })

    newSocket.on('initial_state', (data) => {
      console.log('📦 Nhận initial state:', data)
      setParkingLotMap(data.parking_lot_map || {})
      setStatistics(data.statistics || statistics)
    })

    newSocket.on('parking_update', (data) => {
      // Cập nhật state với dữ liệu mới
      setParkingLotMap(data.parking_lot_map || {})
      setStatistics(data.statistics || statistics)
    })

    newSocket.on('vehicle_exited', (data) => {
      console.log('🚗 Xe đã ra:', data)
      // Có thể hiển thị thông báo hoặc log
    })

    setSocket(newSocket)

    // Cleanup
    return () => {
      newSocket.close()
    }
  }, [socketUrl]) // Reconnect khi socketUrl thay đổi

  return (
    <div className="app">
      <header className="app-header">
        <h1>🚗 Bãi Đỗ Xe - Dashboard Real-time</h1>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? '🟢 Đã kết nối' : '🔴 Chưa kết nối'}
          </div>
          <div style={{ 
            padding: '8px 15px', 
            borderRadius: '20px', 
            background: configMode === 'local' ? '#e3f2fd' : '#fff3e0',
            color: configMode === 'local' ? '#1976d2' : '#f57c00',
            fontSize: '12px',
            fontWeight: '600'
          }}>
            Mode: {configMode === 'local' ? '🏠 Local' : '🌐 Distributed'}
          </div>
        </div>
      </header>

      <Statistics statistics={statistics} />

      <div className="main-content">
        <div className="parking-map-section">
          <h2>🗺️ Bản Đồ Bãi Xe</h2>
          <ParkingMap parkingLotMap={parkingLotMap} />
        </div>

        <div className="vehicle-table-section">
          <h2>📋 Chi Tiết Xe Đang Đỗ</h2>
          <VehicleTable parkingLotMap={parkingLotMap} />
        </div>
      </div>
    </div>
  )
}

export default App
