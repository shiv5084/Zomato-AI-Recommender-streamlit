import { useState } from 'react'
import PreferenceForm from './components/PreferenceForm.jsx'
import RecommendationList from './components/RecommendationList.jsx'
import EmptyState from './components/EmptyState.jsx'
import { getRecommendations } from './services/api.js'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (payload) => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await getRecommendations(payload)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-orange-600 text-white py-5 shadow-sm">
        <div className="max-w-5xl mx-auto px-4">
          <h1 className="text-2xl font-bold">Zomato AI Recommender</h1>
          <p className="text-orange-100 text-sm mt-1">
            Discover the best restaurants powered by AI
          </p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <PreferenceForm onSubmit={handleSubmit} loading={loading} />
          </div>

          <div className="lg:col-span-2">
            {loading && (
              <div className="flex flex-col items-center justify-center py-20 text-gray-500">
                <div className="w-10 h-10 border-4 border-orange-200 border-t-orange-600 rounded-full animate-spin mb-4"></div>
                <p className="text-sm font-medium">Crunching data & consulting the AI...</p>
                <p className="text-xs text-gray-400 mt-1">This may take a few seconds</p>
              </div>
            )}

            {!loading && error && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-4">
                <p className="font-medium">Error</p>
                <p className="text-sm">{error}</p>
              </div>
            )}

            {!loading && !error && !result && (
              <EmptyState
                title="Ready to explore?"
                message="Set your preferences on the left and hit 'Get Recommendations' to see AI-curated restaurant picks."
                icon="🍽️"
              />
            )}

            {!loading && !error && result && (
              <RecommendationList result={result} />
            )}
          </div>
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 py-4 mt-8">
        <div className="max-w-5xl mx-auto px-4 text-center text-xs text-gray-400">
          Zomato AI Recommender &middot; Milestone 1 Demo
        </div>
      </footer>
    </div>
  )
}
