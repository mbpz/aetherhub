import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, X } from 'lucide-react'

let toastQueue = []
let setToastsGlobal = null

export function toast(message, type = 'success') {
  const id = Date.now() + Math.random()
  const newToast = { id, message, type }
  toastQueue = [...toastQueue, newToast]
  if (setToastsGlobal) setToastsGlobal([...toastQueue])
  setTimeout(() => {
    toastQueue = toastQueue.filter((t) => t.id !== id)
    if (setToastsGlobal) setToastsGlobal([...toastQueue])
  }, 3500)
}

export function ToastContainer() {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    setToastsGlobal = setToasts
    return () => { setToastsGlobal = null }
  }, [])

  const remove = (id) => {
    toastQueue = toastQueue.filter((t) => t.id !== id)
    setToasts([...toastQueue])
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium pointer-events-auto max-w-sm
            ${t.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}
        >
          {t.type === 'success' ? <CheckCircle size={16} /> : <XCircle size={16} />}
          <span className="flex-1">{t.message}</span>
          <button onClick={() => remove(t.id)} className="opacity-80 hover:opacity-100">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}
