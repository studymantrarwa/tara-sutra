import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Tara Sutra Astrology",
  description: "Vedic astrology, Kundli, matching, numerology and Panchang."
};

export default function RootLayout({children}:{children:React.ReactNode}) {
  return <html lang="en"><body>{children}</body></html>;
}