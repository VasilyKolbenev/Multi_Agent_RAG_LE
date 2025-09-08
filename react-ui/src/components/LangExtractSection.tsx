import { useState } from 'react'
import { Brain, FileText, Loader2 } from 'lucide-react'

interface LangExtractSectionProps {
  onExtract: (text: string, prompt?: string) => void
  loading: boolean
}

export default function LangExtractSection({ onExtract, loading }: LangExtractSectionProps) {
  const [text, setText] = useState('')
  const [prompt, setPrompt] = useState('Извлеки людей, компании, места, события и даты из этого текста')
  const [file, setFile] = useState<File | null>(null)

  const handleTextExtract = () => {
    if (!text.trim()) return
    onExtract(text, prompt)
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return

    setFile(selectedFile)
    
    try {
      const fileText = await readFileAsText(selectedFile)
      setText(fileText)
    } catch (error) {
      console.error('Error reading file:', error)
      alert('Ошибка чтения файла. Попробуйте другой файл.')
    }
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
      // Динамически загружаем PDF.js
      const pdfjsLib = await import('pdfjs-dist')
      pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`
      
      const arrayBuffer = await file.arrayBuffer()
      const pdf = await pdfjsLib.getDocument(arrayBuffer).promise
      
      let fullText = ''
      
      // Извлекаем текст из всех страниц
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i)
        const textContent = await page.getTextContent()
        const pageText = textContent.items
          .map((item: any) => item.str)
          .join(' ')
        fullText += `\n--- Страница ${i} ---\n${pageText}\n`
      }
      
      return fullText.trim()
    } catch (error) {
      console.error('PDF parsing error:', error)
      throw new Error(`Ошибка парсинга PDF: ${error}`)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
          <Brain className="w-5 h-5" />
          LangExtract - Извлечение сущностей
        </h2>
        <div className="bg-violet-100 text-violet-800 text-xs font-medium px-2.5 py-0.5 rounded">
          Шаг 2
        </div>
      </div>
      
      <div className="bg-violet-50 border border-violet-200 rounded-md p-3 mb-4">
        <p className="text-sm text-violet-800">
          <strong>🧠 Второй шаг:</strong> Извлеките ключевые сущности (имена, компании, места, даты) из загруженных документов. 
          Это поможет улучшить качество поиска на следующем этапе.
        </p>
      </div>
      
      <div className="space-y-4">
        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Загрузить файл (опционально)
          </label>
          <div className="flex items-center gap-3">
            <input
              type="file"
              accept=".txt,.md,.pdf,.doc,.docx,.rtf,.csv,.json,.xml,.html"
              onChange={handleFileUpload}
              className="flex-1 text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {file && (
              <span className="text-sm text-green-600 flex items-center gap-1">
                <FileText className="w-4 h-4" />
                {file.name}
              </span>
            )}
          </div>
        </div>

        {/* Text Input */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Текст для анализа
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Вставьте текст для извлечения сущностей..."
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={8}
          />
        </div>

        {/* Custom Prompt */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Промпт для извлечения (опционально)
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Опишите, что именно нужно извлечь из текста..."
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={3}
          />
        </div>

        {/* Extract Button */}
        <button
          onClick={handleTextExtract}
          disabled={!text.trim() || loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-violet-600 text-white font-medium rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Brain className="w-5 h-5" />
          )}
          🔍 Извлечь сущности
        </button>

        {/* Info */}
        <div className="bg-violet-50 border border-violet-200 rounded-md p-3">
          <h4 className="text-sm font-medium text-violet-900 mb-1">🧠 LangExtract:</h4>
          <p className="text-xs text-violet-800">
            Современная библиотека для извлечения именованных сущностей из текста с использованием LLM.
            Автоматически находит людей, организации, места, даты, события и другие важные элементы.
          </p>
        </div>
      </div>
    </div>
  )
}
