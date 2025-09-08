import { useState, useEffect } from 'react'
import { Search, Upload, Brain } from 'lucide-react'
import SearchSection from './components/SearchSection'
import IngestSection from './components/IngestSection'
import LangExtractSection from './components/LangExtractSection'
import ResultsSection from './components/ResultsSection'
import WorkflowGuide from './components/WorkflowGuide'
import WorkflowStats from './components/WorkflowStats'
import { ApiService } from './services/api'

type WorkflowStep = 'ingest' | 'langextract' | 'search'

interface WorkflowState {
  hasDocuments: boolean
  hasEntities: boolean
  currentStep: WorkflowStep
  completedSteps: WorkflowStep[]
}

function App() {
  const [activeTab, setActiveTab] = useState<WorkflowStep>('ingest')
  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [apiStatus, setApiStatus] = useState<'connecting' | 'connected' | 'error'>('connecting')
  const [workflow, setWorkflow] = useState<WorkflowState>({
    hasDocuments: false,
    hasEntities: false,
    currentStep: 'ingest',
    completedSteps: []
  })

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
      
      // Update workflow state
      setWorkflow(prev => ({
        ...prev,
        hasDocuments: true,
        currentStep: 'langextract',
        completedSteps: [...prev.completedSteps.filter(s => s !== 'ingest'), 'ingest']
      }))
      
      // Auto-switch to next step
      setTimeout(() => setActiveTab('langextract'), 1500)
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
      
      // Update workflow state
      setWorkflow(prev => ({
        ...prev,
        hasEntities: true,
        currentStep: 'search',
        completedSteps: [...prev.completedSteps.filter(s => s !== 'langextract'), 'langextract']
      }))
      
      // Auto-switch to next step
      setTimeout(() => setActiveTab('search'), 1500)
    } catch (error) {
      console.error('LangExtract failed:', error)
      setResults({ error: 'Извлечение сущностей не удалось. Проверьте подключение к API.' })
    } finally {
      setLoading(false)
    }
  }

  const resetWorkflow = () => {
    setWorkflow({
      hasDocuments: false,
      hasEntities: false,
      currentStep: 'ingest',
      completedSteps: []
    })
    setActiveTab('ingest')
    setResults(null)
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
            <div className="flex items-center gap-3">
              {workflow.hasDocuments && (
                <button
                  onClick={resetWorkflow}
                  className="text-sm text-slate-600 hover:text-slate-900 underline"
                >
                  🔄 Начать заново
                </button>
              )}
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

        {/* Workflow Progress */}
        <div className="mb-6">
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
            <h3 className="text-sm font-medium text-slate-700 mb-3">Рабочий процесс RAG системы</h3>
            <div className="flex items-center justify-between">
              {[
                { 
                  id: 'ingest', 
                  label: '1. Загрузка', 
                  icon: Upload, 
                  description: 'Добавьте документы в базу знаний',
                  isCompleted: workflow.completedSteps.includes('ingest'),
                  isActive: workflow.currentStep === 'ingest'
                },
                { 
                  id: 'langextract', 
                  label: '2. Извлечение', 
                  icon: Brain, 
                  description: 'Извлеките ключевые сущности',
                  isCompleted: workflow.completedSteps.includes('langextract'),
                  isActive: workflow.currentStep === 'langextract',
                  isDisabled: !workflow.hasDocuments
                },
                { 
                  id: 'search', 
                  label: '3. Поиск', 
                  icon: Search, 
                  description: 'Задавайте вопросы системе',
                  isCompleted: false,
                  isActive: workflow.currentStep === 'search',
                  isDisabled: !workflow.hasDocuments
                }
              ].map(({ id, label, icon: Icon, description, isCompleted, isActive, isDisabled }, index) => (
                <div key={id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center">
                    <button
                      onClick={() => !isDisabled && setActiveTab(id as WorkflowStep)}
                      disabled={isDisabled}
                      className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                        isCompleted
                          ? 'bg-green-500 text-white'
                          : isActive
                          ? 'bg-blue-500 text-white'
                          : isDisabled
                          ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                          : 'bg-slate-300 text-slate-600 hover:bg-slate-400'
                      }`}
                    >
                      {isCompleted ? (
                        <div className="w-3 h-3 border-2 border-white rounded-full bg-white" />
                      ) : (
                        <Icon className="w-4 h-4" />
                      )}
                    </button>
                    <div className="mt-2 text-center">
                      <div className={`text-xs font-medium ${
                        isActive ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-slate-500'
                      }`}>
                        {label}
                      </div>
                      <div className="text-xs text-slate-400 mt-1 max-w-20">
                        {description}
                      </div>
                    </div>
                  </div>
                  {index < 2 && (
                    <div className={`flex-1 h-0.5 mx-4 ${
                      isCompleted ? 'bg-green-300' : 'bg-slate-200'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="mb-6">
          <div className="flex space-x-1 bg-slate-200 rounded-lg p-1">
            {[
              { id: 'ingest', label: 'Загрузка', icon: Upload },
              { id: 'langextract', label: 'Извлечение сущностей', icon: Brain },
              { id: 'search', label: 'Поиск', icon: Search }
            ].map(({ id, label, icon: Icon }) => {
              const isDisabled = (id === 'langextract' || id === 'search') && !workflow.hasDocuments
              return (
                <button
                  key={id}
                  onClick={() => !isDisabled && setActiveTab(id as WorkflowStep)}
                  disabled={isDisabled}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-all ${
                    activeTab === id
                      ? 'bg-white text-slate-900 shadow-sm'
                      : isDisabled
                      ? 'text-slate-400 cursor-not-allowed'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                  {workflow.completedSteps.includes(id as WorkflowStep) && (
                    <div className="w-2 h-2 bg-green-500 rounded-full" />
                  )}
                </button>
              )
            })}
          </div>
        </nav>

        {/* Main Content */}
        {activeTab === 'search' ? (
          /* Search Layout - Full Width */
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Search Form */}
              <div className="lg:col-span-3">
                <SearchSection onSearch={handleSearch} loading={loading} />
              </div>
              
              {/* Workflow Stats - Compact */}
              <div>
                <WorkflowStats 
                  hasDocuments={workflow.hasDocuments}
                  hasEntities={workflow.hasEntities}
                  completedSteps={workflow.completedSteps}
                />
              </div>
            </div>
            
            {/* Search Results - Full Width */}
            <div className="w-full">
              <ResultsSection results={results} loading={loading} activeTab={activeTab} />
            </div>
          </div>
        ) : (
          /* Other Tabs Layout - 3 Column */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Panel - Input */}
            <div className="lg:col-span-2 space-y-6">
              {activeTab === 'ingest' && (
                <IngestSection onIngest={handleIngest} loading={loading} />
              )}
              {activeTab === 'langextract' && (
                <LangExtractSection onExtract={handleLangExtract} loading={loading} />
              )}
            </div>

            {/* Right Panel - Guide & Results */}
            <div className="space-y-6">
              <WorkflowStats 
                hasDocuments={workflow.hasDocuments}
                hasEntities={workflow.hasEntities}
                completedSteps={workflow.completedSteps}
              />
              <WorkflowGuide 
                currentStep={workflow.currentStep}
                hasDocuments={workflow.hasDocuments}
                hasEntities={workflow.hasEntities}
              />
              {(activeTab === 'ingest' || activeTab === 'langextract') && (
                <ResultsSection results={results} loading={loading} activeTab={activeTab} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
