import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PredictX - Hybrid Prediction Markets",
  description: "Trade on future events with crypto. Off-chain matching, on-chain settlement.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
