import { useState, useEffect } from 'react'
import { 
  Upload, 
  FileText, 
  Trash2, 
  Loader2, 
  Plus, 
  X,
  AlertCircle,
  CheckCircle,
  FolderOpen,
  Brain
} from 'lucide-react'
import { ApiService } from '../services/api'

interface Document {
  id: string
  name: string
  size?: number
  created?: string
}

interface DocumentSidebarProps {
  onDocumentsChange?: () => void
}

export default function DocumentSidebar({ onDocumentsChange }: DocumentSidebarProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const [autoExtract, setAutoExtract] = useState(false)
  const [notification, setNotification] = useState<{
    type: 'success' | 'error'
    message: string
  } | null>(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const docs = await ApiService.getDocuments()
      // Сервер может вернуть массив строк doc_id либо объектов
      const formattedDocs = (Array.isArray(docs) ? docs : []).map((doc: any, index: number) => {
        if (typeof doc === 'string') {
          return { id: doc, name: doc, size: undefined, created: undefined }
        }
        return {
          id: doc.doc_id || doc.id || `doc_${index}`,
          name: doc.name || doc.doc_id || `Документ ${index + 1}`,
          size: doc.text_length,
          created: doc.created
        }
      })
      setDocuments(formattedDocs)
    } catch (error) {
      console.error('Failed to load documents:', error)
      showNotification('error', 'Не удалось загрузить список документов')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (files: FileList) => {
    if (files.length === 0) return

    try {
      setUploading(true)

      // Для текстовых файлов можем отправить пачкой
      const textLike: File[] = []
      const binaryLike: File[] = []
      Array.from(files).forEach(f => {
        const name = f.name.toLowerCase()
        if (name.endsWith('.txt') || name.endsWith('.md') || name.endsWith('.rtf') || name.endsWith('.csv') || name.endsWith('.json') || name.endsWith('.xml') || name.endsWith('.html')) {
          textLike.push(f)
        } else {
          binaryLike.push(f)
        }
      })

      if (textLike.length > 0) {
        const result = await ApiService.ingest(textLike as unknown as FileList)
        showNotification('success', `Загружено текстовых: ${result.count}`)
      }

      // Для PDF/DOCX и др. извлекаем текст на сервере, затем добавляем через /ingest (text)
      for (const file of binaryLike) {
        try {
          const extracted = await ApiService.extractText(file)
          const text = extracted.text || ''
          if (text.trim()) {
            const docId = `file_${file.name}_${Date.now().toString(36)}`
            await ApiService.ingest(null, text, docId)
          } else {
            console.warn('Extracted empty text for', file.name)
          }
        } catch (e) {
          console.error('ExtractText failed for', file.name, e)
        }
      }

      // Если включено автоизвлечение сущностей — просто покажем уведомление; серверные эндпоинты уже готовы
      if (autoExtract) {
        showNotification('success', 'Извлечение сущностей включено. Можно запустить его в соответствующем разделе.')
      }

      await loadDocuments()
      onDocumentsChange?.()
      setShowUpload(false)
    } catch (error) {
      console.error('Upload failed:', error)
      showNotification('error', 'Ошибка при загрузке файлов')
    } finally {
      setUploading(false)
    }
  }

  const handleTextUpload = async (text: string) => {
    if (!text.trim()) return

    try {
      setUploading(true)
      const result = await ApiService.ingest(null, text)
      
      showNotification('success', 'Текст успешно добавлен')
      await loadDocuments()
      onDocumentsChange?.()
      setShowUpload(false)
    } catch (error) {
      console.error('Text upload failed:', error)
      showNotification('error', 'Ошибка при добавлении текста')
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteDocument = async (docId: string) => {
    if (!confirm('Удалить этот документ?')) return

    try {
      await ApiService.deleteDocument(docId)
      showNotification('success', 'Документ удален')
      await loadDocuments()
      onDocumentsChange?.()
    } catch (error) {
      console.error('Delete failed:', error)
      showNotification('error', 'Ошибка при удалении документа')
    }
  }

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message })
    setTimeout(() => setNotification(null), 3000)
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Неизвестно'
    if (bytes < 1024) return `${bytes} Б`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`
    return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`
  }

  return (
    <div className="w-80 bg-white border-r border-slate-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2">
            <FolderOpen className="w-5 h-5" />
            Документы
          </h2>
          <button
            onClick={() => setShowUpload(true)}
            className="p-2 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="Добавить документы"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
        <div className="flex items-center justify-between mt-2">
          <div className="text-sm text-slate-500">
            {documents.length} документов
          </div>
          <button
            onClick={loadDocuments}
            className="text-xs text-slate-500 hover:text-slate-700 underline"
          >
            Обновить
          </button>
        </div>
        
        
      </div>

      {/* Notification */}
      {notification && (
        <div className={`mx-4 mt-4 p-3 rounded-lg flex items-center gap-2 ${
          notification.type === 'success' 
            ? 'bg-green-50 text-green-800 border border-green-200'
            : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          {notification.type === 'success' ? (
            <CheckCircle className="w-4 h-4" />
          ) : (
            <AlertCircle className="w-4 h-4" />
          )}
          <span className="text-sm">{notification.message}</span>
        </div>
      )}

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
          </div>
        ) : documents.length === 0 ? (
          <div className="p-4 text-center text-slate-500">
            <FileText className="w-12 h-12 mx-auto mb-3 text-slate-300" />
            <p className="text-sm">Пока нет документов</p>
            <p className="text-xs mt-1">Добавьте файлы для начала работы</p>
          </div>
        ) : (
          <div className="p-4 space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="group p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <span className="text-sm font-medium text-slate-900 truncate">
                        {doc.name}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      {formatFileSize(doc.size)}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteDocument(doc.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-600 transition-all"
                    title="Удалить документ"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-96 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <h3 className="font-semibold text-slate-900">Добавить документы</h3>
              <button
                onClick={() => setShowUpload(false)}
                className="p-1 text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-4 space-y-4">
              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Загрузить файлы
                </label>
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
                  <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <input
                    type="file"
                    multiple
                    accept=".txt,.md,.pdf,.doc,.docx,.rtf,.csv,.json,.xml,.html"
                    onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                    className="hidden"
                    id="file-upload"
                    disabled={uploading}
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer text-blue-600 hover:text-blue-700 text-sm font-medium"
                  >
                    Выберите файлы
                  </label>
                  <p className="text-xs text-slate-500 mt-1">
                    PDF, DOC, TXT, MD и другие
                  </p>
                </div>
              </div>

              {/* Text Input */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Или добавить текст
                </label>
                <textarea
                  placeholder="Вставьте текст здесь..."
                  className="w-full h-32 px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.ctrlKey) {
                      const target = e.target as HTMLTextAreaElement
                      handleTextUpload(target.value)
                      target.value = ''
                    }
                  }}
                  disabled={uploading}
                />
                <div className="flex justify-between items-center mt-2">
                  <p className="text-xs text-slate-500">
                    Ctrl+Enter для добавления
                  </p>
                  <button
                    onClick={(e) => {
                      const textarea = e.currentTarget.parentElement?.previousElementSibling as HTMLTextAreaElement
                      if (textarea) {
                        handleTextUpload(textarea.value)
                        textarea.value = ''
                      }
                    }}
                    disabled={uploading}
                    className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    Добавить
                  </button>
                </div>
              </div>

              {/* Auto Extract Option */}
              <div className="border-t border-slate-200 pt-4">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={autoExtract}
                    onChange={(e) => setAutoExtract(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    disabled={uploading}
                  />
                  <Brain className="w-4 h-4 text-slate-500" />
                  <span className="text-slate-700">Автоматически извлекать сущности</span>
                </label>
                <p className="text-xs text-slate-500 mt-1 ml-6">
                  Улучшает качество поиска, но замедляет загрузку
                </p>
              </div>

              {uploading && (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                  <span className="ml-2 text-sm text-slate-600">Загрузка...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

