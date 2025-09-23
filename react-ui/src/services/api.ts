const API_BASE = import.meta.env.VITE_API_BASE || 'https://multi-agent-rag-le-git-main-vasilys-projects-d04563ed.vercel.app'

export class ApiService {
  static async health() {
    const response = await fetch(`${API_BASE}/health`)
    if (!response.ok) throw new Error('API not available')
    return response.json()
  }

  static async search(query: string, k = 10) {
    const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&k=${k}`)
    if (!response.ok) throw new Error('Search failed')
    return response.json()
  }

  static async askAgentic(query: string, maxIterations = 5) {
    const response = await fetch(`${API_BASE}/ask/agentic?q=${encodeURIComponent(query)}&max_iterations=${maxIterations}`)
    if (!response.ok) throw new Error('Agentic search failed')
    return response.json()
  }

  static async askAgenticStream(query: string, maxIterations = 5) {
    const response = await fetch(`${API_BASE}/ask/agentic/stream?q=${encodeURIComponent(query)}&max_iterations=${maxIterations}`)
    if (!response.ok) throw new Error('Agentic stream failed')
    return response.body
  }

  static async searchByEntities(query: string, entities: string) {
    const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&entities=${encodeURIComponent(entities)}`)
    if (!response.ok) throw new Error('Entity search failed')
    return response.json()
  }

  static async ingest(files?: FileList | null, text?: string, docId?: string) {
    const formData = new FormData()
    
    if (files) {
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i])
      }
    }
    
    if (text) {
      formData.append('text', text)
      if (docId) formData.append('doc_id', docId)
    }

    const response = await fetch(`${API_BASE}/ingest`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) throw new Error('Ingest failed')
    return response.json()
  }

  static async langExtract(text: string, taskPrompt?: string, docId = 'react_ui_doc') {
    const response = await fetch(`${API_BASE}/langextract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text,
        task_prompt: taskPrompt || 'Извлеки людей, компании, места, события и даты из этого текста',
        doc_id: docId
      })
    })
    
    if (!response.ok) throw new Error('LangExtract failed')
    return response.json()
  }

  static async getDocuments() {
    const response = await fetch(`${API_BASE}/documents`)
    if (!response.ok) throw new Error('Failed to get documents')
    return response.json()
  }

  static async deleteDocument(docId: string) {
    const response = await fetch(`${API_BASE}/documents/${docId}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error('Failed to delete document')
    return response.json()
  }

  static async getEntityAnalytics() {
    const response = await fetch(`${API_BASE}/analytics/entities`)
    if (!response.ok) throw new Error('Failed to get entity analytics')
    return response.json()
  }
}
