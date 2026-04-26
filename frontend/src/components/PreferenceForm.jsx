import { useState, useEffect } from 'react'
import { getCities, getCuisines } from '../services/api.js'

const BUDGET_BANDS = [
  { value: 'low', label: 'Low (up to Rs. 500)' },
  { value: 'medium', label: 'Medium (Rs. 500 - 1500)' },
  { value: 'high', label: 'High (above Rs. 1500)' },
]

export default function PreferenceForm({ onSubmit, loading }) {
  const [location, setLocation] = useState('')
  const [budgetBand, setBudgetBand] = useState('medium')
  const [cuisines, setCuisines] = useState([])
  const [minimumRating, setMinimumRating] = useState(4.0)
  const [additionalPreferences, setAdditionalPreferences] = useState('')
  const [cities, setCities] = useState([])
  const [allCuisines, setAllCuisines] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    getCities().then(data => setCities(data.items)).catch(() => setCities([]))
    getCuisines().then(data => setAllCuisines(data.items)).catch(() => setAllCuisines([]))
  }, [])

  const toggleCuisine = (c) => {
    setCuisines(prev =>
      prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
    )
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setError(null)
    if (!location) {
      setError('Please select a location.')
      return
    }
    onSubmit({
      location,
      budget_band: budgetBand,
      cuisines,
      minimum_rating: minimumRating,
      additional_preferences: additionalPreferences || null,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md space-y-5">
      <h2 className="text-xl font-semibold text-gray-900">Find Restaurants</h2>

      {error && (
        <div className="bg-red-50 text-red-700 px-4 py-2 rounded text-sm">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
        <select
          value={location}
          onChange={e => setLocation(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
        >
          <option value="">Select a city...</option>
          {cities.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Budget Band</label>
        <div className="flex gap-3">
          {BUDGET_BANDS.map(b => (
            <button
              key={b.value}
              type="button"
              onClick={() => setBudgetBand(b.value)}
              className={`flex-1 py-2 rounded-md border text-sm font-medium transition ${
                budgetBand === b.value
                  ? 'bg-orange-500 text-white border-orange-500'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-orange-400'
              }`}
            >
              {b.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Minimum Rating: <span className="text-orange-600 font-bold">{minimumRating}</span>
        </label>
        <input
          type="range"
          min="0"
          max="5"
          step="0.1"
          value={minimumRating}
          onChange={e => setMinimumRating(parseFloat(e.target.value))}
          className="w-full accent-orange-500"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Any</span>
          <span>5.0</span>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Cuisines (optional)</label>
        <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto border border-gray-200 rounded-md p-2">
          {allCuisines.slice(0, 50).map(c => (
            <button
              key={c}
              type="button"
              onClick={() => toggleCuisine(c)}
              className={`px-3 py-1 rounded-full text-xs border transition ${
                cuisines.includes(c)
                  ? 'bg-orange-100 text-orange-800 border-orange-300'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-orange-300'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
        {allCuisines.length > 50 && (
          <p className="text-xs text-gray-400 mt-1">Showing 50 of {allCuisines.length} cuisines.</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Additional Preferences (optional)</label>
        <textarea
          value={additionalPreferences}
          onChange={e => setAdditionalPreferences(e.target.value)}
          placeholder="E.g. outdoor seating, vegetarian friendly..."
          rows={3}
          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-orange-600 hover:bg-orange-700 text-white font-semibold py-2.5 rounded-md transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Finding recommendations...' : 'Get Recommendations'}
      </button>
    </form>
  )
}
