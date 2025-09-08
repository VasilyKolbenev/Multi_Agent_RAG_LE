import { useState, useRef } from 'react'
import { Upload, FileText, Loader2, X } from 'lucide-react'

interface IngestSectionProps {
  onIngest: (files: FileList | null, text?: string) => void
  loading: boolean
}

export default function IngestSection({ onIngest, loading }: IngestSectionProps) {
  const [text, setText] = useState('')
  const [docTitle, setDocTitle] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFiles(e.dataTransfer.files)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(e.target.files)
    }
  }

  const handleTextSubmit = () => {
    if (!text.trim()) return
    onIngest(null, text)
  }

  const handleFileSubmit = () => {
    if (!selectedFiles || selectedFiles.length === 0) return
    onIngest(selectedFiles)
  }

  const clearFiles = () => {
    setSelectedFiles(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-6">
      {/* Text Ingest */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Добавить текст
          </h2>
          <div className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
            Шаг 1
          </div>
        </div>
        
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
          <p className="text-sm text-blue-800">
            <strong>💡 Начните здесь:</strong> Добавьте документы в базу знаний, чтобы система могла с ними работать. 
            После успешной загрузки вы автоматически перейдете к следующему шагу.
          </p>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Название документа (опционально)
            </label>
            <input
              type="text"
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="Название документа"
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Текст документа
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Вставьте текст документа..."
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={6}
            />
          </div>
          
          <button
            onClick={handleTextSubmit}
            disabled={!text.trim() || loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <FileText className="w-5 h-5" />
            )}
            📚 Добавить текст в базу знаний
          </button>
        </div>
      </div>

      {/* File Ingest */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Загрузить файлы
          </h2>
          <div className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
            Шаг 1
          </div>
        </div>
        
        <div className="space-y-4">
          {/* Drag & Drop Zone */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-slate-300 hover:border-slate-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-lg font-medium text-slate-700 mb-2">
              Перетащите файлы сюда
            </p>
            <p className="text-sm text-slate-500 mb-4">
              или нажмите для выбора
            </p>
            <p className="text-xs text-slate-400">
              Поддерживаются: TXT, MD, PDF, DOC, DOCX, RTF, CSV, JSON, XML, HTML
            </p>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".txt,.md,.pdf,.doc,.docx,.rtf,.csv,.json,.xml,.html"
            onChange={handleFileSelect}
            className="hidden"
          />

          {/* Selected Files */}
          {selectedFiles && selectedFiles.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-blue-900">
                  Выбранные файлы ({selectedFiles.length})
                </h4>
                <button
                  onClick={clearFiles}
                  className="text-blue-600 hover:text-blue-800"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="space-y-1">
                {Array.from(selectedFiles).map((file, index) => (
                  <div key={index} className="text-sm text-blue-800 flex items-center gap-2">
                    <FileText className="w-3 h-3" />
                    {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={handleFileSubmit}
            disabled={!selectedFiles || selectedFiles.length === 0 || loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Upload className="w-5 h-5" />
            )}
            📤 Загрузить файлы в базу знаний
          </button>
        </div>
      </div>
    </div>
  )
}
