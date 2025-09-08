import { FileText, Brain, Search, CheckCircle } from 'lucide-react'

interface WorkflowStatsProps {
  hasDocuments: boolean
  hasEntities: boolean
  completedSteps: string[]
}

export default function WorkflowStats({ hasDocuments, hasEntities, completedSteps }: WorkflowStatsProps) {
  const stats = [
    {
      label: 'Документы загружены',
      value: hasDocuments,
      icon: FileText,
      color: 'blue'
    },
    {
      label: 'Сущности извлечены',
      value: hasEntities,
      icon: Brain,
      color: 'violet'
    },
    {
      label: 'Готово к поиску',
      value: hasDocuments,
      icon: Search,
      color: 'emerald'
    }
  ]

  const progress = (completedSteps.length / 3) * 100

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-slate-700">Прогресс настройки</h3>
        <div className="text-xs text-slate-500">
          {completedSteps.length}/3 шагов
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-slate-200 rounded-full h-2 mb-4">
        <div 
          className="bg-gradient-to-r from-blue-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Stats grid */}
      <div className="space-y-3">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          const colorClasses = {
            blue: stat.value ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-400',
            violet: stat.value ? 'bg-violet-100 text-violet-700' : 'bg-slate-100 text-slate-400',
            emerald: stat.value ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-400'
          }[stat.color]

          return (
            <div key={index} className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${colorClasses}`}>
                {stat.value ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <div className="flex-1">
                <div className={`text-sm font-medium ${
                  stat.value ? 'text-slate-900' : 'text-slate-500'
                }`}>
                  {stat.label}
                </div>
              </div>
              {stat.value && (
                <CheckCircle className="w-4 h-4 text-green-500" />
              )}
            </div>
          )
        })}
      </div>

      {hasDocuments && (
        <div className="mt-4 pt-4 border-t border-slate-200">
          <div className="text-xs text-center text-slate-500">
            🎉 Система готова к работе!
          </div>
        </div>
      )}
    </div>
  )
}
