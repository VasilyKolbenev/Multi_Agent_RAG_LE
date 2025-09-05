import { Loader2, AlertCircle, CheckCircle, FileText, Tags, Brain } from 'lucide-react'

interface ResultsSectionProps {
  results: any
  loading: boolean
  activeTab: 'search' | 'ingest' | 'langextract'
}

export default function ResultsSection({ results, loading, activeTab }: ResultsSectionProps) {
  const renderSearchResults = () => {
    if (!results || (!results.answer && !results.length)) return null

    // Agentic RAG результат
    if (results.answer) {
      return (
        <div className="space-y-4">
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
            <h3 className="font-medium text-emerald-900 mb-2 flex items-center gap-2">
              <Brain className="w-4 h-4" />
              Ответ агентной системы
            </h3>
            <div className="prose prose-sm max-w-none text-emerald-800">
              {results.answer.split('\n').map((line: string, index: number) => (
                <p key={index} className="mb-2">{line}</p>
              ))}
            </div>
          </div>
          
          {results.sources && results.sources.length > 0 && (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <h4 className="font-medium text-slate-900 mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Источники ({results.sources.length})
              </h4>
              <div className="space-y-2">
                {results.sources.map((source: any, index: number) => (
                  <div key={index} className="bg-white border border-slate-200 rounded p-3">
                    <div className="text-sm font-medium text-slate-900 mb-1">
                      {source.doc_id} (релевантность: {(source.score * 100).toFixed(1)}%)
                    </div>
                    <div className="text-sm text-slate-600">
                      {source.content?.substring(0, 200)}...
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )
    }

    // Обычные результаты поиска
    if (Array.isArray(results)) {
      return (
        <div className="space-y-3">
          <h3 className="font-medium text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Найденные фрагменты ({results.length})
          </h3>
          {results.map((result: any, index: number) => (
            <div key={index} className="bg-white border border-slate-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-900">{result.doc_id}</span>
                <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">
                  {(result.score * 100).toFixed(1)}%
                </span>
              </div>
              <p className="text-sm text-slate-600">
                {result.content || result.text || 'Содержимое недоступно'}
              </p>
            </div>
          ))}
        </div>
      )
    }

    return null
  }

  const renderLangExtractResults = () => {
    if (!results || !results.items) return null

    const groupedEntities = results.items.reduce((acc: any, item: any) => {
      const type = item.type || 'other'
      if (!acc[type]) acc[type] = []
      acc[type].push(item)
      return acc
    }, {})

    const typeColors: { [key: string]: string } = {
      person: 'bg-blue-100 text-blue-800 border-blue-200',
      organization: 'bg-green-100 text-green-800 border-green-200',
      location: 'bg-purple-100 text-purple-800 border-purple-200',
      date: 'bg-orange-100 text-orange-800 border-orange-200',
      money: 'bg-red-100 text-red-800 border-red-200',
      other: 'bg-gray-100 text-gray-800 border-gray-200'
    }

    const typeIcons: { [key: string]: string } = {
      person: '👤',
      organization: '🏢',
      location: '📍',
      date: '📅',
      money: '💰',
      other: '🏷️'
    }

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-slate-900 flex items-center gap-2">
            <Tags className="w-4 h-4" />
            Извлеченные сущности ({results.items.length})
          </h3>
          {results.success && (
            <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              Успешно
            </span>
          )}
        </div>

        {Object.entries(groupedEntities).map(([type, entities]: [string, any]) => (
          <div key={type} className="bg-white border border-slate-200 rounded-lg p-4">
            <h4 className="font-medium text-slate-900 mb-3 flex items-center gap-2">
              <span>{typeIcons[type] || '🏷️'}</span>
              {type.charAt(0).toUpperCase() + type.slice(1)} ({entities.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {entities.map((entity: any, index: number) => (
                <span
                  key={index}
                  className={`px-2 py-1 rounded text-xs font-medium border ${
                    typeColors[type] || typeColors.other
                  }`}
                >
                  {entity.value}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderIngestResults = () => {
    if (!results) return null

    if (results.error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-800">
            <AlertCircle className="w-4 h-4" />
            <span className="font-medium">Ошибка загрузки</span>
          </div>
          <p className="text-red-700 mt-1">{results.error}</p>
        </div>
      )
    }

    if (results.success) {
      return (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-green-800">
            <CheckCircle className="w-4 h-4" />
            <span className="font-medium">Успешно загружено</span>
          </div>
          <p className="text-green-700 mt-1">{results.message}</p>
        </div>
      )
    }

    return null
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
            <p className="text-slate-600">
              {activeTab === 'search' && 'Поиск по базе знаний...'}
              {activeTab === 'ingest' && 'Загрузка данных...'}
              {activeTab === 'langextract' && 'Извлечение сущностей...'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="text-center py-8">
          <div className="text-slate-400 mb-2">
            {activeTab === 'search' && <FileText className="w-12 h-12 mx-auto" />}
            {activeTab === 'ingest' && <CheckCircle className="w-12 h-12 mx-auto" />}
            {activeTab === 'langextract' && <Tags className="w-12 h-12 mx-auto" />}
          </div>
          <p className="text-slate-600">
            {activeTab === 'search' && 'Результаты поиска появятся здесь'}
            {activeTab === 'ingest' && 'Статус загрузки появится здесь'}
            {activeTab === 'langextract' && 'Извлеченные сущности появятся здесь'}
          </p>
        </div>
      </div>
    )
  }

  if (results.error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-800">
            <AlertCircle className="w-4 h-4" />
            <span className="font-medium">Ошибка</span>
          </div>
          <p className="text-red-700 mt-1">{results.error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      {activeTab === 'search' && renderSearchResults()}
      {activeTab === 'ingest' && renderIngestResults()}
      {activeTab === 'langextract' && renderLangExtractResults()}
    </div>
  )
}
