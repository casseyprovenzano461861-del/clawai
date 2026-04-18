import React from 'react'
import ReactDOM from 'react-dom/client'
import AppRouter from './AppRouter.jsx'
import { WebSocketProvider } from './context/WebSocketContext.jsx'
import { ToastProvider } from './context/ToastContext.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ToastProvider>
      <WebSocketProvider>
        <AppRouter />
      </WebSocketProvider>
    </ToastProvider>
  </React.StrictMode>,
)
