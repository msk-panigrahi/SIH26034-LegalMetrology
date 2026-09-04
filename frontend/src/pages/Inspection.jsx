import { useState, useRef, useCallback } from 'react'
import './Inspection.css'

const API_BASE = '/api'

const CATEGORIES = [
  { value: 'food', label: 'Food' },
  { value: 'beverage', label: 'Beverage' },
  { value: 'cosmetic', label: 'Cosmetic' },
  { value: 'pharmaceutical', label: 'Pharmaceutical' },
  { value: 'electronics', label: 'Electronics' },
  { value: 'textile', label: 'Textile' },
  { value: 'household', label: 'Household' },
  { value: 'other', label: 'Other' },
]

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_SIZE_MB = 10

export default function Inspection() {
  const [productName, setProductName] = useState('')
  const [category, setCategory] = useState('other')
  const [notes, setNotes] = useState('')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  // ---- File handling ----

  const handleFile = useCallback((f) => {
    setError('')
    setResult(null)

    if (!f) return

    if (!ALLOWED_TYPES.includes(f.type)) {
      setError(`Unsupported format. Allowed: JPG, PNG, WEBP.`)
      return
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File too large. Maximum size is ${MAX_SIZE_MB} MB.`)
      return
    }

    setFile(f)
    setPreview(URL.createObjectURL(f))
  }, [])

  const onDrop = useCallback(
    (e) => {
      e.preventDefault()
      setDragOver(false)
      const f = e.dataTransfer.files?.[0]
      handleFile(f)
    },
    [handleFile]
  )

  const onDragOver = (e) => {
    e.preventDefault()
    setDragOver(true)
  }

  const onDragLeave = () => setDragOver(false)

  const removeFile = () => {
    setFile(null)
    setPreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // ---- Upload ----

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!file) {
      setError('Please select an image to upload.')
      return
    }

    setUploading(true)
    setError('')
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    if (productName.trim()) formData.append('product_name', productName.trim())
    formData.append('product_category', category)
    if (notes.trim()) formData.append('notes', notes.trim())

    try {
      const res = await fetch(`${API_BASE}/inspections/upload`, {
        method: 'POST',
        body: formData,
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Upload failed.')
      }

      setResult(data)
      // Reset form but keep the result visible
      setProductName('')
      setCategory('other')
      setNotes('')
      setFile(null)
      setPreview(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err) {
      setError(err.message || 'Something went wrong.')
    } finally {
      setUploading(false)
    }
  }

  // ---- Render ----

  return (
    <div className="inspection-page">
      <h2>New Inspection</h2>
      <p className="page-desc">
        Upload a package image to create an inspection record.
      </p>

      {error && <div className="message error">{error}</div>}

      {result && (
        <div className="result-card" style={{ marginBottom: 24 }}>
          <h3>✅ Inspection Created</h3>
          <div className="result-grid">
            <div className="result-item">
              <span className="label">Inspection ID</span>
              <span className="value">#{result.inspection_id}</span>
            </div>
            <div className="result-item">
              <span className="label">Status</span>
              <span className="value">
                <span className="status-badge">{result.status}</span>
              </span>
            </div>
            <div className="result-item">
              <span className="label">Filename</span>
              <span className="value">{result.filename}</span>
            </div>
            {result.product && (
              <>
                <div className="result-item">
                  <span className="label">Product</span>
                  <span className="value">{result.product.product_name}</span>
                </div>
                <div className="result-item">
                  <span className="label">Category</span>
                  <span className="value">{result.product.category}</span>
                </div>
              </>
            )}
            {result.notes && (
              <div className="result-item">
                <span className="label">Notes</span>
                <span className="value">{result.notes}</span>
              </div>
            )}
          </div>
        </div>
      )}

      <form className="upload-form" onSubmit={handleSubmit}>
        {/* Image drop zone */}
        <div
          className={`dropzone ${dragOver ? 'dragover' : ''}`}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={() => fileInputRef.current?.click()}
        >
          {preview ? (
            <div className="image-preview-wrapper">
              <img src={preview} alt="Preview" className="image-preview" />
              <button
                type="button"
                className="remove-image-btn"
                onClick={(e) => {
                  e.stopPropagation()
                  removeFile()
                }}
              >
                ✕
              </button>
            </div>
          ) : (
            <>
              <div className="dropzone-icon">📷</div>
              <p className="dropzone-text">
                <strong>Click to browse</strong> or drag & drop an image
              </p>
              <p className="dropzone-hint">JPG, PNG, or WEBP — max {MAX_SIZE_MB} MB</p>
            </>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.webp"
            hidden
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
        </div>

        {/* Product name */}
        <div className="form-row-inline">
          <div className="form-row">
            <label htmlFor="product-name">Product Name</label>
            <input
              id="product-name"
              type="text"
              placeholder="e.g. Tata Salt 1kg"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
            />
          </div>
          <div className="form-row">
            <label htmlFor="category">Category</label>
            <select
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Notes */}
        <div className="form-row">
          <label htmlFor="notes">Inspection Notes</label>
          <textarea
            id="notes"
            placeholder="Any observations about the package…"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        {/* Submit */}
        <button type="submit" className="submit-btn" disabled={uploading}>
          {uploading && <span className="spinner" />}
          {uploading ? 'Uploading…' : 'Upload & Create Inspection'}
        </button>
      </form>
    </div>
  )
}
