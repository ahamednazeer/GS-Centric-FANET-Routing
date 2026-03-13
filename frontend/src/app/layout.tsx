import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
    variable: "--font-inter",
    subsets: ["latin"],
});

export const metadata: Metadata = {
    title: "GS-Centric FANET Routing Console",
    description: "Directed GS-rooted routing control plane for FANET operations",
};

export const viewport: Viewport = {
    themeColor: "#0f172a",
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={`${inter.variable} font-sans antialiased`}>
                {children}
            </body>
        </html>
    );
}
