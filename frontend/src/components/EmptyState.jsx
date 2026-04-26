export default function EmptyState({ title, message, icon = '🔍' }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-10 text-center">
      <div className="text-4xl mb-3">{icon}</div>
      <p className="text-lg font-medium text-gray-800 mb-1">{title}</p>
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  )
}
