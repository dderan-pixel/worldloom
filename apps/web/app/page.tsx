import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold">PredictX</h1>
              </div>
              <div className="ml-6 flex space-x-8">
                <Link href="/markets" className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900">
                  Markets
                </Link>
                <Link href="/portfolio" className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-900">
                  Portfolio
                </Link>
              </div>
            </div>
            <div className="flex items-center">
              <button className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700">
                Connect Wallet
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Hybrid Prediction Markets
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Trade on future events with crypto. Off-chain matching, on-chain settlement.
          </p>
          <div className="flex justify-center gap-4">
            <Link
              href="/markets"
              className="bg-blue-600 text-white px-6 py-3 rounded-md text-base font-medium hover:bg-blue-700"
            >
              Browse Markets
            </Link>
            <Link
              href="/portfolio"
              className="bg-white text-blue-600 border border-blue-600 px-6 py-3 rounded-md text-base font-medium hover:bg-blue-50"
            >
              View Portfolio
            </Link>
          </div>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-3">
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-2">Fast Trading</h3>
            <p className="text-gray-600">Off-chain orderbook for instant matching and low latency</p>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-2">Secure Custody</h3>
            <p className="text-gray-600">Your funds stay on-chain in smart contracts you control</p>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-2">Fair Settlement</h3>
            <p className="text-gray-600">Transparent on-chain settlement and dispute resolution</p>
          </div>
        </div>
      </main>
    </div>
  );
}
