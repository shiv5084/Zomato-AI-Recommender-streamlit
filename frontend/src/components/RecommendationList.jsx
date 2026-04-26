import RestaurantCard from './RestaurantCard.jsx'

export default function RecommendationList({ result }) {
  const { rankings, source, candidate_count, filter_count } = result

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Recommendations</h2>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span className="bg-gray-100 px-2 py-1 rounded">
            {rankings.length} of {candidate_count} candidates
          </span>
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            source === 'llm'
              ? 'bg-green-100 text-green-700'
              : source === 'fallback'
              ? 'bg-yellow-100 text-yellow-700'
              : 'bg-gray-100 text-gray-600'
          }`}>
            {source === 'llm' ? 'AI Ranked' : source === 'fallback' ? 'Fallback' : 'No Matches'}
          </span>
        </div>
      </div>

      {rankings.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
          <p className="text-lg font-medium text-gray-700 mb-1">No restaurants found</p>
          <p className="text-sm">Try relaxing your filters (lower rating, broader budget, or different cuisines).</p>
        </div>
      ) : (
        <div className="space-y-4">
          {rankings.map(r => (
            <RestaurantCard
              key={r.restaurant_id}
              rank={r.rank}
              restaurant={r.restaurant}
              explanation={r.explanation}
            />
          ))}
        </div>
      )}
    </div>
  )
}
