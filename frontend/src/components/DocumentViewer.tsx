import { useEffect, useState } from 'react'

interface DocumentViewerProps {
  documentUrl: string
  onClose: () => void
  isOpen: boolean
}

export default function DocumentViewer({ documentUrl, onClose, isOpen }: DocumentViewerProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showFallback, setShowFallback] = useState(false)

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setLoading(true)
      setError(null)
      setShowFallback(false)
    }
  }, [isOpen])

  // Handle ESC key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  // Handle iframe load
  const handleIframeLoad = () => {
    setLoading(false)
  }

  // Handle iframe error
  const handleIframeError = () => {
    setLoading(false)
    setError('Não foi possível carregar a visualização do documento.')
    setShowFallback(true)
  }

  // Check if document is .docx (which typically doesn't preview well in iframes)
  const isDocxFile = documentUrl.toLowerCase().includes('.doc')

  // Handle download
  const handleDownload = () => {
    window.open(documentUrl, '_blank')
  }

  // Handle backdrop click to close
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      {/* Modal Container */}
      <div className="relative w-full h-full max-w-7xl max-h-[90vh] m-4 bg-white rounded-lg shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
          <h2 className="text-xl font-semibold text-gray-900">Visualização do Documento</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
            aria-label="Fechar"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 relative overflow-hidden">
          {/* Loading State */}
          {loading && !showFallback && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
                <p className="mt-4 text-gray-600">Carregando documento...</p>
              </div>
            </div>
          )}

          {/* Error State or .docx Fallback */}
          {(error || showFallback || isDocxFile) && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50 p-8">
              <div className="text-center max-w-md">
                <div className="mx-auto w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mb-4">
                  <svg
                    className="w-8 h-8 text-yellow-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Visualização não disponível
                </h3>
                <p className="text-gray-600 mb-6">
                  {error ||
                    'Arquivos .doc/.docx não podem ser visualizados diretamente no navegador. Por favor, faça o download do documento para visualizá-lo.'}
                </p>
                <button
                  onClick={handleDownload}
                  className="inline-flex items-center px-6 py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-lg font-medium shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  Baixar Documento
                </button>
              </div>
            </div>
          )}

          {/* Iframe for document preview (for non-.docx files) */}
          {!isDocxFile && !showFallback && (
            <iframe
              src={documentUrl}
              className="w-full h-full border-0"
              title="Document Preview"
              onLoad={handleIframeLoad}
              onError={handleIframeError}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
          <p className="text-sm text-gray-600">
            Pressione <kbd className="px-2 py-1 bg-white border border-gray-300 rounded text-xs">ESC</kbd> ou clique fora para fechar
          </p>
          <div className="flex space-x-3">
            <button
              onClick={handleDownload}
              className="inline-flex items-center px-4 py-2 bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 rounded-lg text-sm font-medium shadow-sm hover:shadow transition-all duration-200"
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              Baixar
            </button>
            <button
              onClick={onClose}
              className="inline-flex items-center px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-medium shadow-sm hover:shadow transition-all duration-200"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
