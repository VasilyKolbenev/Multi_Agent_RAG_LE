import { useState } from 'react'
import { Brain, FileText, Loader2, Upload, X, CheckCircle } from 'lucide-react'

interface LangExtractSectionProps {
  onExtract: (text: string, prompt?: string) => void
  loading: boolean
}

interface ProcessedFile {
  file: File
  status: 'processing' | 'completed' | 'error'
  text?: string
  error?: string
}

export default function LangExtractSection({ onExtract, loading }: LangExtractSectionProps) {
  const [processedFiles, setProcessedFiles] = useState<ProcessedFile[]>([])
  const [prompt, setPrompt] = useState('Извлеки людей, компании, места, события и даты из всех загруженных документов')
  const [combinedText, setCombinedText] = useState('')

  const handleFilesUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length === 0) return

    // Добавляем файлы в список для обработки
    const newFiles: ProcessedFile[] = files.map(file => ({
      file,
      status: 'processing'
    }))
    
    setProcessedFiles(prev => [...prev, ...newFiles])

    // Обрабатываем каждый файл
    for (const fileItem of newFiles) {
      try {
        const text = await readFileAsText(fileItem.file)
        
        setProcessedFiles(prev => {
          const updated = prev.map(f => 
            f.file === fileItem.file 
              ? { ...f, status: 'completed', text }
              : f
          )
          // Обновляем объединенный текст после изменения состояния
          setTimeout(() => {
            const completedFiles = updated.filter(f => f.status === 'completed' && f.text)
            const combined = completedFiles
              .map(f => `\n=== ${f.file.name} ===\n${f.text}`)
              .join('\n\n')
            setCombinedText(combined)
          }, 0)
          return updated
        })
      } catch (error) {
        setProcessedFiles(prev => prev.map(f => 
          f.file === fileItem.file 
            ? { ...f, status: 'error', error: String(error) }
            : f
        ))
      }
    }
  }

  const updateCombinedText = () => {
    const completedFiles = processedFiles.filter(f => f.status === 'completed' && f.text)
    const combined = completedFiles
      .map(f => `\n=== ${f.file.name} ===\n${f.text}`)
      .join('\n\n')
    setCombinedText(combined)
  }

  const removeFile = (fileToRemove: File) => {
    setProcessedFiles(prev => {
      const updated = prev.filter(f => f.file !== fileToRemove)
      // Обновляем объединенный текст
      const completedFiles = updated.filter(f => f.status === 'completed' && f.text)
      const combined = completedFiles
        .map(f => `\n=== ${f.file.name} ===\n${f.text}`)
        .join('\n\n')
      setCombinedText(combined)
      return updated
    })
  }

  const handleExtract = () => {
    if (!combinedText.trim()) return
    onExtract(combinedText, prompt)
  }

  const readFileAsText = async (file: File): Promise<string> => {
    // Проверяем тип файла
    if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
      return await parsePDF(file)
    }
    
    // Для остальных файлов используем стандартное чтение
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result
        if (typeof result === 'string') {
          resolve(result)
        } else {
          reject(new Error('Failed to read file as text'))
        }
      }
      reader.onerror = () => reject(new Error('File reading error'))
      reader.readAsText(file, 'utf-8')
    })
  }

  const parsePDF = async (file: File): Promise<string> => {
    try {
      // Сначала пробуем серверную обработку
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('/api/extract-pdf-text', {
        method: 'POST',
        body: formData
      })
      
      if (response.ok) {
        const result = await response.json()
        return result.text || 'PDF обработан, но текст не найден'
      }
      
      // Если сервер недоступен, используем клиентскую обработку
      throw new Error('Сервер недоступен, пробуем клиентскую обработку')
      
    } catch (error) {
      console.warn('Server PDF processing failed, trying client-side:', error)
      
      // Клиентская обработка с локальным worker
      try {
        const pdfjsLib = await import('pdfjs-dist')
        
        // Используем локальный worker из node_modules
        pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
          'pdfjs-dist/build/pdf.worker.min.js',
          import.meta.url
        ).toString()
        
        const arrayBuffer = await file.arrayBuffer()
        const pdf = await pdfjsLib.getDocument({
          data: arrayBuffer,
          verbosity: 0 // Отключаем лишние логи
        }).promise
        
        let fullText = ''
        
        for (let i = 1; i <= pdf.numPages; i++) {
          try {
            const page = await pdf.getPage(i)
            const textContent = await page.getTextContent()
            const pageText = textContent.items
              .filter((item: any) => item.str && item.str.trim())
              .map((item: any) => item.str)
              .join(' ')
            
            if (pageText.trim()) {
              fullText += `\n--- Страница ${i} ---\n${pageText.trim()}\n`
            }
          } catch (pageError) {
            console.warn(`Ошибка обработки страницы ${i}:`, pageError)
            fullText += `\n--- Страница ${i} ---\n[Ошибка извлечения текста]\n`
          }
        }
        
        return fullText.trim() || 'PDF файл не содержит извлекаемого текста'
        
      } catch (clientError) {
        console.error('Client-side PDF parsing failed:', clientError)
        throw new Error(`Не удалось обработать PDF файл. Возможно, файл поврежден или защищен паролем. Ошибка: ${clientError}`)
      }
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
          <Brain className="w-5 h-5" />
          Извлечение сущностей из документов
        </h2>
        <div className="bg-violet-100 text-violet-800 text-xs font-medium px-2.5 py-0.5 rounded">
          Шаг 2
        </div>
      </div>
      
      <div className="bg-violet-50 border border-violet-200 rounded-md p-3 mb-6">
        <p className="text-sm text-violet-800">
          <strong>🧠 Второй шаг:</strong> Загрузите все необходимые документы. Система автоматически извлечет текст и найдет ключевые сущности для улучшения поиска.
        </p>
      </div>
      
      <div className="space-y-6">
        {/* Multiple File Upload */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-3">
            Загрузите документы для анализа
          </label>
          <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:border-violet-400 transition-colors">
            <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <div className="mb-4">
              <input
                type="file"
                multiple
                accept=".txt,.md,.pdf,.doc,.docx,.rtf,.csv,.json,.xml,.html"
                onChange={handleFilesUpload}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer bg-violet-600 text-white px-6 py-2 rounded-lg hover:bg-violet-700 transition-colors"
              >
                Выберите файлы
              </label>
            </div>
            <p className="text-sm text-slate-500">
              Поддерживаются: PDF, DOC, DOCX, TXT, MD, RTF, CSV, JSON, XML, HTML
            </p>
          </div>
        </div>

        {/* Processed Files List */}
        {processedFiles.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-slate-700 mb-3">
              Обработанные файлы ({processedFiles.length})
            </h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {processedFiles.map((fileItem, index) => (
                <div key={index} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                  <div className="flex-shrink-0">
                    {fileItem.status === 'processing' && (
                      <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                    )}
                    {fileItem.status === 'completed' && (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    )}
                    {fileItem.status === 'error' && (
                      <X className="w-4 h-4 text-red-500" />
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-slate-900 truncate">
                      {fileItem.file.name}
                    </div>
                    <div className="text-xs text-slate-500">
                      {(fileItem.file.size / 1024).toFixed(1)} KB
                      {fileItem.status === 'completed' && fileItem.text && (
                        <span className="ml-2">• {fileItem.text.length} символов</span>
                      )}
                      {fileItem.status === 'error' && (
                        <span className="ml-2 text-red-600">• {fileItem.error}</span>
                      )}
                    </div>
                  </div>
                  
                  <button
                    onClick={() => removeFile(fileItem.file)}
                    className="flex-shrink-0 text-slate-400 hover:text-red-500 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Combined Text Preview */}
        {combinedText && (
          <div>
            <h3 className="text-sm font-medium text-slate-700 mb-3">
              Объединенный текст для анализа
            </h3>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 max-h-40 overflow-y-auto">
              <pre className="text-xs text-slate-600 whitespace-pre-wrap">
                {combinedText.slice(0, 1000)}
                {combinedText.length > 1000 && '...\n\n[Показано первые 1000 символов]'}
              </pre>
            </div>
            <div className="text-xs text-slate-500 mt-2">
              Всего символов: {combinedText.length}
            </div>
          </div>
        )}

        {/* Custom Prompt */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Инструкция для извлечения сущностей
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Опишите, какие сущности нужно извлечь..."
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none"
            rows={3}
          />
        </div>

        {/* Extract Button */}
        <button
          onClick={handleExtract}
          disabled={!combinedText.trim() || loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-violet-600 text-white font-medium rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Brain className="w-5 h-5" />
          )}
          🔍 Извлечь сущности из всех документов
        </button>

        {/* Info */}
        <div className="bg-violet-50 border border-violet-200 rounded-md p-3">
          <h4 className="text-sm font-medium text-violet-900 mb-1">💡 Как это работает:</h4>
          <ul className="text-xs text-violet-800 space-y-1">
            <li>• Загружайте несколько документов одновременно</li>
            <li>• Система автоматически извлечет текст из всех форматов</li>
            <li>• AI найдет людей, компании, места, даты и события</li>
            <li>• Результаты улучшат качество поиска на следующем шаге</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
