export default function PortfolioPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold mb-6">My Portfolio</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-xl font-semibold mb-4">Balances</h2>
          <p className="text-gray-600">Connect your wallet to view balances</p>
        </div>
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-xl font-semibold mb-4">Positions</h2>
          <p className="text-gray-600">Connect your wallet to view positions</p>
        </div>
      </div>
    </div>
  );
}
