import { useState, useEffect } from 'react'
import { Wifi, WifiOff, Loader2 } from 'lucide-react'
import ChatInterface from './components/ChatInterface'
import DocumentSidebar from './components/DocumentSidebar'
import { ApiService } from './services/api'

function App() {
  const [apiStatus, setApiStatus] = useState<'connecting' | 'connected' | 'error'>('connecting')

  useEffect(() => {
    checkApiStatus()
  }, [])

  const checkApiStatus = async () => {
    try {
      await ApiService.health()
      setApiStatus('connected')
    } catch (error) {
      setApiStatus('error')
      console.error('API connection failed:', error)
    }
  }

  const handleDocumentsChange = () => {
    // Можно добавить логику обновления при изменении документов
    console.log('Documents changed')
  }

  if (apiStatus === 'connecting') {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Подключение к API...</h2>
          <p className="text-slate-600">Проверяем соединение с сервером</p>
        </div>
      </div>
    )
  }

  if (apiStatus === 'error') {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <WifiOff className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Ошибка подключения</h2>
          <p className="text-slate-600 mb-4">
            Не удалось подключиться к серверу. Проверьте настройки API или попробуйте позже.
          </p>
          <button
            onClick={checkApiStatus}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex bg-slate-50">
        {/* Header */}
      <div className="fixed top-0 left-0 right-0 bg-white border-b border-slate-200 z-10">
        <div className="flex items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AI</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900">ДИТ ИИ‑эксперт</h1>
              <p className="text-xs text-slate-500">Интеллектуальная работа с документами</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2 px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm">
            <Wifi className="w-4 h-4" />
            <span>Подключено</span>
          </div>
        </div>
          </div>

        {/* Main Content */}
      <div className="flex flex-1 pt-16">
        {/* Document Sidebar */}
        <DocumentSidebar onDocumentsChange={handleDocumentsChange} />
        
        {/* Chat Interface */}
        <div className="flex-1">
          <ChatInterface onDocumentsChange={handleDocumentsChange} />
          </div>
      </div>
    </div>
  )
}

export default App
