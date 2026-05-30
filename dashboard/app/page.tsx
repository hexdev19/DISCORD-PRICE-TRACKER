import { SiteNav } from "@/components/landing/site-nav";
import { AuthNotice } from "@/components/landing/auth-notice";
import { Hero } from "@/components/landing/hero";
import { PriceTicker } from "@/components/landing/price-ticker";
import { Features } from "@/components/landing/features";
import { HowItWorks } from "@/components/landing/how-it-works";
import { DashboardPreview } from "@/components/landing/dashboard-preview";
import { FinalCta } from "@/components/landing/final-cta";
import { SiteFooter } from "@/components/landing/site-footer";

export default function Home() {
  return (
    <>
      <SiteNav />
      <AuthNotice />
      <main>
        <Hero />
        <PriceTicker />
        <Features />
        <HowItWorks />
        <DashboardPreview />
        <FinalCta />
      </main>
      <SiteFooter />
    </>
  );
}
