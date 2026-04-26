export default function RestaurantCard({ rank, restaurant, explanation }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-5 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-3">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-orange-100 text-orange-700 font-bold text-sm">
            {rank}
          </span>
          <h3 className="text-lg font-semibold text-gray-900">{restaurant.restaurant_name}</h3>
        </div>
        <span className="text-sm font-medium text-gray-500 capitalize bg-gray-100 px-2 py-1 rounded">
          {restaurant.budget_band}
        </span>
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {restaurant.cuisines.map(c => (
          <span key={c} className="text-xs bg-orange-50 text-orange-700 px-2 py-0.5 rounded-full border border-orange-100">
            {c}
          </span>
        ))}
      </div>

      <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
        <span className="flex items-center gap-1">
          <span className="text-yellow-500">&#9733;</span>
          {restaurant.rating ?? 'N/A'}
        </span>
        <span>|</span>
        <span>Rs. {restaurant.approx_cost_for_two_inr ?? 'N/A'} for two</span>
        <span>|</span>
        <span>{restaurant.city}</span>
      </div>

      <div className="bg-gray-50 rounded-md p-3 text-sm text-gray-700 border-l-4 border-orange-400">
        <span className="font-medium text-gray-900">Why:</span>{' '}
        {explanation}
      </div>
    </div>
  )
}
