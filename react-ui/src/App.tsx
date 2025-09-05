import { useState, useEffect } from 'react'
import { Search, Upload, Brain } from 'lucide-react'
import SearchSection from './components/SearchSection'
import IngestSection from './components/IngestSection'
import LangExtractSection from './components/LangExtractSection'
import ResultsSection from './components/ResultsSection'
import { ApiService } from './services/api'

function App() {
  const [activeTab, setActiveTab] = useState<'search' | 'ingest' | 'langextract'>('search')
  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(false)
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

  const handleSearch = async (query: string, type: 'intelligent' | 'fragments' | 'entities', entities?: string) => {
    setLoading(true)
    try {
      let result
      switch (type) {
        case 'intelligent':
          result = await ApiService.askAgentic(query)
          break
        case 'fragments':
          result = await ApiService.search(query)
          break
        case 'entities':
          result = await ApiService.searchByEntities(query, entities || '')
          break
      }
      setResults(result)
    } catch (error) {
      console.error('Search failed:', error)
      setResults({ error: 'Поиск не удался. Проверьте подключение к API.' })
    } finally {
      setLoading(false)
    }
  }

  const handleIngest = async (files: FileList | null, text?: string) => {
    setLoading(true)
    try {
      const result = await ApiService.ingest(files, text)
      setResults({ success: true, message: `Загружено: ${result.count} элементов` })
    } catch (error) {
      console.error('Ingest failed:', error)
      setResults({ error: 'Загрузка не удалась. Проверьте подключение к API.' })
    } finally {
      setLoading(false)
    }
  }

  const handleLangExtract = async (text: string, prompt?: string) => {
    setLoading(true)
    try {
      const result = await ApiService.langExtract(text, prompt)
      setResults(result)
    } catch (error) {
      console.error('LangExtract failed:', error)
      setResults({ error: 'Извлечение сущностей не удалось. Проверьте подключение к API.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
                🚀 MultiAgent‑RAG Pro
                <span className="text-sm font-normal text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
                  React UI v1.0
                </span>
              </h1>
              <p className="text-slate-600 mt-1">Современный интерфейс для многоагентного RAG поиска</p>
            </div>
            <div className="flex items-center gap-2">
              <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${{
                connecting: 'bg-yellow-100 text-yellow-700',
                connected: 'bg-green-100 text-green-700',
                error: 'bg-red-100 text-red-700'
              }[apiStatus]}`}>
                <div className={`w-2 h-2 rounded-full ${{
                  connecting: 'bg-yellow-500 animate-pulse',
                  connected: 'bg-green-500',
                  error: 'bg-red-500'
                }[apiStatus]}`} />
                API: {apiStatus === 'connected' ? 'Подключен' : apiStatus === 'connecting' ? 'Подключение...' : 'Ошибка'}
              </div>
            </div>
          </div>
        </header>

        {/* Navigation Tabs */}
        <nav className="mb-6">
          <div className="flex space-x-1 bg-slate-200 rounded-lg p-1">
            {[
              { id: 'search', label: 'Поиск', icon: Search },
              { id: 'ingest', label: 'Загрузка', icon: Upload },
              { id: 'langextract', label: 'Извлечение сущностей', icon: Brain }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-all ${
                  activeTab === id
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>
        </nav>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel - Input */}
          <div className="space-y-6">
            {activeTab === 'search' && (
              <SearchSection onSearch={handleSearch} loading={loading} />
            )}
            {activeTab === 'ingest' && (
              <IngestSection onIngest={handleIngest} loading={loading} />
            )}
            {activeTab === 'langextract' && (
              <LangExtractSection onExtract={handleLangExtract} loading={loading} />
            )}
          </div>

          {/* Right Panel - Results */}
          <div>
            <ResultsSection results={results} loading={loading} activeTab={activeTab} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
