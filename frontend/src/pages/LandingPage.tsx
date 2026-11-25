import { useEffect, useState } from 'react';
import { APP_URL } from '../App';

// What the UniCounsel app really offers, one line each, in the order a student meets them.
const TOOLS = [
  { title: 'University matches', copy: 'Programmes ranked against your grades, budget and preferred countries.' },
  { title: 'Cost calculator', copy: 'Tuition, rent and living costs added up for each city you are considering.' },
  { title: 'Fee comparison', copy: 'Side-by-side fees for the universities on your shortlist.' },
  { title: 'Scholarship finder', copy: 'Scholarships you can apply for, filtered by country and field.' },
  { title: 'Visa checklist and odds', copy: 'The documents each visa needs and a rough read on your chances.' },
  { title: 'Housing and city safety', copy: 'Places to stay near campus and what the area is like.' },
  { title: 'Course to career', copy: 'Where a programme tends to lead, and what jobs pay in that market.' },
  { title: 'Interview practice and resume', copy: 'Practise admission interviews and build a resume in the same place.' },
];

const STEPS = [
  { art: '/illustrations/uc-how-profile.webp', title: 'Tell us about you', copy: 'Grades, budget, the countries you like and what you want to study.' },
  { art: '/illustrations/uc-how-map.webp', title: 'See your matches', copy: 'A shortlist of programmes that fit, on a map and in a list.' },
  { art: '/illustrations/uc-how-compare.webp', title: 'Compare the real cost', copy: 'Fees, living costs and scholarships, side by side.' },
  { art: '/illustrations/uc-how-documents.webp', title: 'Get your papers ready', copy: 'Visa checklist, resume and interview practice before you apply.' },
];

// Read from the UniCounsel app, which counts them from the data it actually searches.
function useDatasetCounts() {
  const [counts, setCounts] = useState<{ universities: number; countries: number; names: string } | null>(null);
  useEffect(() => {
    fetch(`${APP_URL}/api/site-counts`)
      .then((r) => r.json())
      .then((d) => setCounts({ universities: d.universities, countries: d.countries, names: d.country_names }))
      .catch(() => setCounts(null));
  }, []);
  return counts;
}

const LandingPage = () => {
  const counts = useDatasetCounts();
  const go = (path: string) => `${APP_URL}${path}`;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <a href="/" className="flex items-center gap-2 text-lg font-semibold">
            <img src="/apple-touch-icon.png" alt="" width={32} height={32} className="rounded-lg" /> UniCounsel
          </a>
          <nav className="flex items-center gap-6 text-sm">
            <a href="#how" className="text-muted-foreground hover:text-foreground">How it works</a>
            <a href="#tools" className="text-muted-foreground hover:text-foreground">Tools</a>
            <a href={go('/login')} className="text-muted-foreground hover:text-foreground">Sign in</a>
            <a href={go('/signup')} className="rounded-full bg-primary px-4 py-2 font-medium text-primary-foreground hover:opacity-90">Create account</a>
          </nav>
        </div>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl items-center gap-8 px-6 py-12 lg:grid-cols-[1.25fr_1fr] lg:gap-12 lg:py-16">
          <div>
            <h1 className="font-display text-4xl font-semibold leading-[1.1] sm:text-5xl lg:text-[3rem]">Choose where to study, with the numbers in front of you.</h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-muted-foreground">
              UniCounsel matches you with programmes abroad, adds up what they really cost, and walks you through the visa and
              paperwork that follows.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <a href={go('/signup')} className="rounded-full bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:opacity-90">Find my matches</a>
              <a href="#how" className="rounded-full border border-border px-6 py-3 text-sm font-medium hover:border-primary/60">How it works</a>
            </div>
            {counts && counts.universities > 0 && (
              <dl className="mt-8 flex gap-10 border-t border-border pt-6">
                <div><dt className="text-sm text-muted-foreground">Universities listed</dt><dd className="text-3xl font-semibold">{counts.universities.toLocaleString()}</dd></div>
                <div><dt className="text-sm text-muted-foreground">Countries</dt><dd className="text-3xl font-semibold">{counts.countries.toLocaleString()}</dd></div>
              </dl>
            )}
          </div>
          <div className="aspect-[4/3] w-full overflow-hidden rounded-2xl border border-border bg-card">
            <img src="/illustrations/uc-hero.webp" alt="Campus buildings from several countries joined by a flight path" width={1200} height={675} className="h-full w-full scale-[1.12] object-cover object-[50%_85%]" />
          </div>
        </section>

        <section id="how" className="border-t border-border">
          <div className="mx-auto max-w-6xl px-6 py-14">
            <h2 className="font-display text-3xl font-semibold sm:text-4xl">How it works</h2>
            <ol className="mt-10 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
              {STEPS.map((s, i) => (
                <li key={s.title}>
                  <img src={s.art} alt="" width={300} height={300} loading="lazy" className="mb-6 h-36 w-auto object-contain" />
                  <p className="text-xs font-medium text-primary">Step {i + 1}</p>
                  <h3 className="mt-1 text-lg font-semibold">{s.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{s.copy}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="tools" className="border-t border-border">
          <div className="mx-auto max-w-6xl px-6 py-14">
            <h2 className="font-display text-3xl font-semibold sm:text-4xl">What is inside</h2>
            <div className="mt-10 grid border-t border-border sm:grid-cols-2">
              {TOOLS.map((t) => (
                <div key={t.title} className="border-b border-border py-6 pr-10">
                  <h3 className="font-semibold">{t.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{t.copy}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-border">
          <div className="mx-auto max-w-6xl px-6 py-14 text-center">
            <h2 className="font-display text-3xl font-semibold sm:text-4xl">Start with your shortlist.</h2>
            <p className="mx-auto mt-4 max-w-lg text-muted-foreground">It takes a few minutes to set up your profile. You can change it any time.</p>
            <a href={go('/signup')} className="mt-8 inline-flex rounded-full bg-primary px-7 py-3 text-sm font-medium text-primary-foreground hover:opacity-90">Create your account</a>
          </div>
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-8 text-sm text-muted-foreground">
          <span>UniCounsel</span>
          <span>Fees and visa rules change; always confirm with the university and embassy.</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
