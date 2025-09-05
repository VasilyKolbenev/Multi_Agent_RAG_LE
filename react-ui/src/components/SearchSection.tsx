import { useState } from 'react'
import { Search, Sparkles, FileSearch, Tags, Loader2 } from 'lucide-react'

interface SearchSectionProps {
  onSearch: (query: string, type: 'intelligent' | 'fragments' | 'entities', entities?: string) => void
  loading: boolean
}

export default function SearchSection({ onSearch, loading }: SearchSectionProps) {
  const [query, setQuery] = useState('')
  const [entities, setEntities] = useState('')

  const handleSubmit = (type: 'intelligent' | 'fragments' | 'entities') => {
    if (!query.trim()) return
    onSearch(query, type, entities)
  }

  const handleKeyPress = (e: React.KeyboardEvent, type: 'intelligent' | 'fragments' | 'entities') => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit(type)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center gap-2">
        <Search className="w-5 h-5" />
        Поиск по базе знаний
      </h2>
      
      <div className="space-y-4">
        {/* Search Query */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Поисковый запрос
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => handleKeyPress(e, 'intelligent')}
            placeholder="Введите ваш вопрос..."
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={3}
          />
          <p className="text-xs text-slate-500 mt-1">
            💡 Совет: Используйте Ctrl+Enter для быстрого поиска
          </p>
        </div>

        {/* Entity Filter */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Фильтр по сущностям (опционально)
          </label>
          <input
            type="text"
            value={entities}
            onChange={(e) => setEntities(e.target.value)}
            placeholder="Например: ACME, Иванов, Москва"
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-xs text-slate-500 mt-1">
            Введите сущности через запятую для фильтрации результатов
          </p>
        </div>

        {/* Search Buttons */}
        <div className="space-y-3">
          <button
            onClick={() => handleSubmit('intelligent')}
            disabled={!query.trim() || loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Sparkles className="w-5 h-5" />
            )}
            🚀 Умный ответ (Agentic RAG)
          </button>
          
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => handleSubmit('fragments')}
              disabled={!query.trim() || loading}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <FileSearch className="w-4 h-4" />
              Найти фрагменты
            </button>
            
            <button
              onClick={() => handleSubmit('entities')}
              disabled={!query.trim() || loading}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Tags className="w-4 h-4" />
              По сущностям
            </button>
          </div>
        </div>

        {/* Search Tips */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <h4 className="text-sm font-medium text-blue-900 mb-1">💡 Типы поиска:</h4>
          <ul className="text-xs text-blue-800 space-y-1">
            <li><strong>Умный ответ:</strong> Многоагентный анализ с развернутым ответом</li>
            <li><strong>Найти фрагменты:</strong> Поиск похожих фрагментов документов</li>
            <li><strong>По сущностям:</strong> Поиск по именам, компаниям, местам</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
