import { CheckCircle, Circle, ArrowRight } from 'lucide-react'

interface WorkflowGuideProps {
  currentStep: 'ingest' | 'langextract' | 'search'
  hasDocuments: boolean
  hasEntities: boolean
}

export default function WorkflowGuide({ currentStep, hasDocuments, hasEntities }: WorkflowGuideProps) {
  const steps = [
    {
      id: 'ingest',
      title: 'Загрузка документов',
      description: 'Добавьте документы или текст в базу знаний системы',
      isCompleted: hasDocuments,
      isActive: currentStep === 'ingest',
      tips: [
        'Поддерживаются форматы: TXT, PDF, DOC, DOCX, MD',
        'Можно загружать несколько файлов одновременно',
        'Также можно вставить текст напрямую'
      ]
    },
    {
      id: 'langextract',
      title: 'Извлечение сущностей',
      description: 'Выделите ключевые сущности для улучшения поиска',
      isCompleted: hasEntities,
      isActive: currentStep === 'langextract',
      isDisabled: !hasDocuments,
      tips: [
        'Автоматически находит имена, компании, места, даты',
        'Можно настроить промпт для специфических задач',
        'Результаты используются для фильтрации поиска'
      ]
    },
    {
      id: 'search',
      title: 'Поиск и анализ',
      description: 'Задавайте вопросы и получайте умные ответы',
      isCompleted: false,
      isActive: currentStep === 'search',
      isDisabled: !hasDocuments,
      tips: [
        'Умный ответ - полный анализ с использованием агентов',
        'Поиск фрагментов - быстрое нахождение релевантного контента',
        'Поиск по сущностям - фильтрация по именам, компаниям'
      ]
    }
  ]

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
        🎯 Руководство по работе с системой
      </h3>
      
      <div className="space-y-4">
        {steps.map((step, index) => (
          <div key={step.id} className="flex gap-4">
            {/* Step indicator */}
            <div className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                step.isCompleted
                  ? 'bg-green-500 text-white'
                  : step.isActive
                  ? 'bg-blue-500 text-white'
                  : step.isDisabled
                  ? 'bg-slate-200 text-slate-400'
                  : 'bg-slate-300 text-slate-600'
              }`}>
                {step.isCompleted ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <Circle className="w-4 h-4" />
                )}
              </div>
              {index < steps.length - 1 && (
                <div className={`w-0.5 h-8 mt-2 ${
                  step.isCompleted ? 'bg-green-300' : 'bg-slate-200'
                }`} />
              )}
            </div>
            
            {/* Step content */}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h4 className={`font-medium ${
                  step.isActive ? 'text-blue-700' : step.isCompleted ? 'text-green-700' : 'text-slate-600'
                }`}>
                  {step.title}
                </h4>
                {step.isActive && (
                  <ArrowRight className="w-4 h-4 text-blue-500" />
                )}
              </div>
              
              <p className="text-sm text-slate-600 mb-2">
                {step.description}
              </p>
              
              {step.isActive && (
                <div className="bg-white rounded-md p-3 border border-slate-200">
                  <h5 className="text-xs font-medium text-slate-700 mb-2">💡 Полезные советы:</h5>
                  <ul className="text-xs text-slate-600 space-y-1">
                    {step.tips.map((tip, tipIndex) => (
                      <li key={tipIndex} className="flex items-start gap-2">
                        <span className="text-blue-500 mt-1">•</span>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {step.isDisabled && (
                <div className="text-xs text-slate-400 italic">
                  Сначала завершите предыдущий шаг
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-6 p-4 bg-white rounded-md border border-blue-200">
        <h4 className="text-sm font-medium text-blue-900 mb-2">🚀 Что такое MultiAgent RAG?</h4>
        <p className="text-sm text-blue-800">
          Это система, которая использует несколько AI-агентов для анализа ваших документов. 
          Каждый агент специализируется на определенной задаче: поиск информации, анализ контекста, 
          синтез ответов. Результат - более точные и развернутые ответы на ваши вопросы.
        </p>
      </div>
    </div>
  )
}
