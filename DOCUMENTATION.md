# Ramlatech Website — Complete Technical Documentation
> Version 2.0 · Last updated: April 14, 2026
> Maintained by: Kareem AlWazir (kareem@ramlatech.com)

---

## 1. Live URLs

| Page | URL |
|------|-----|
| Home | https://ramlatech.com |
| About | https://ramlatech.com/about.html |
| Services | https://ramlatech.com/services.html |
| Contact | https://ramlatech.com/contact.html |
| Thank You | https://ramlatech.com/thanks.html |
| Blog (planned) | https://ramlatech.com/blog.html |
| GitHub Pages (fallback) | https://kareem499.github.io/ramlatech-website |

---

## 2. Hosting & Deployment

| Item | Details |
|------|---------|
| Hosting provider | GitHub Pages |
| Repository | https://github.com/Kareem499/ramlatech-website |
| GitHub account | Kareem499 |
| Branch | main |
| Deploy trigger | Auto-deploys on every push to main |
| Pages settings | https://github.com/Kareem499/ramlatech-website/settings/pages |
| Custom domain | ramlatech.com |
| HTTPS | Enforced via GitHub Pages |
| Deploy time | ~60 seconds after push |

### Git Credentials
| Item | Value |
|------|-------|
| Username | Kareem499 |
| Token name | ramlatech-website-token |
| Token expiry | April 2027 |
| Token scope | repo (ramlatech-website only) |
| Token location | Save in password manager — shown once only |

### Daily Deployment Workflow
```bash
cd "/Users/kareamelwazir/Desktop/Ramlatech/Brand Ramlatech/ramlatech"
git add .
git commit -m "type: description"
git push
# Site updates in ~60 seconds at ramlatech.com
```

### Commit Message Types
| Type | Use for |
|------|---------|
| feat | New feature or page |
| fix | Bug fix |
| design | Visual or UI change |
| content | Copy or text update |
| docs | Documentation update |
| seo | SEO improvements |

---

## 3. File Structure

```
ramlatech/
├── index.html          # Home page
├── about.html          # About — story, mission, values
├── services.html       # All 9 services in detail
├── contact.html        # Contact form + RFP form + booking
├── thanks.html         # Thank you page after form submission
├── blog.html           # Blog page (planned)
├── main.css            # Shared design system and styles
├── main.js             # Shared JS — nav, scroll reveal, burger menu
├── sitemap.xml         # XML sitemap for search engines
├── robots.txt          # Search engine crawl instructions
├── CNAME               # Custom domain file — contains: ramlatech.com
├── DOCUMENTATION.md    # This file
└── assets/
    ├── logo-nav.png        # Full logo — white text on navy — navbar
    ├── logo-white.png      # Full logo — white version — footer
    ├── mark-navy.png       # Arch mark — favicon
    ├── mark-white.png      # Arch mark — heritage section, booking card
    └── clients/            # Client logo SVGs (15 files) — used in logo carousel
        ├── 1 Paltel.svg
        ├── 2 Jawwal.svg
        ├── 3 Reach.svg
        ├── 4 Palestinian Authority.svg
        ├── 5 PCBS.svg
        ├── 6 MTIT .svg
        ├── 7 PMA.svg
        ├── 8 World Bank.svg
        ├── 9 Bank of Palestine.svg
        ├── 10 Fine HH.svg
        ├── 11 NFPC.svg
        ├── 12 AlQuds Pharma.svg
        ├── 13 GIZ.svg
        ├── 14 Munib & Angela Masri Logo.svg
        └── 15 Upliftt.svg
```

---

## 4. Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Plain HTML, CSS, JavaScript — no framework |
| Fonts | Google Fonts — Space Grotesk, Inter, JetBrains Mono |
| Icons | Custom inline SVGs — no icon library |
| Hosting | GitHub Pages |
| Forms | Formspree |
| Email marketing | MailerLite |
| Analytics | Google Analytics 4 |
| Booking | Google Calendar |
| Build process | None — static files, deploy directly |

---

## 5. Brand Guidelines

| Element | Value |
|---------|-------|
| Navy | #0E1F38 |
| Gold | #C4882B |
| Teal | #0B8A8A |
| Olive | #4B7A45 |
| Sand | #E8D9BC |
| Ink | #1A1A2E |
| Stone | #6B7280 |
| Pearl | #FAF8F4 |
| White | #FFFFFF |
| Display font | Space Grotesk (Google Fonts) |
| Body font | Inter (Google Fonts) |
| Mono font | JetBrains Mono (Google Fonts) |
| Tagline | Rooted in Heritage. Driven by Innovation. |
| Primary CTA color | Gold #C4882B |
| CTA text color | White #FFFFFF |

---

## 6. Forms — Formspree

| Item | Details |
|------|---------|
| Account email | kareem@ramlatech.com |
| Project dashboard | https://formspree.io/projects/2978224252848700890/overview |

### Contact Form
| Item | Value |
|------|-------|
| Form name | Ramlatech Contact |
| Form ID | xrerzepn |
| Endpoint | https://formspree.io/f/xrerzepn |
| Method | Native HTML POST |
| Required fields | First name, email, message |
| Submissions sent to | kareem@ramlatech.com |

### RFP Form
| Item | Value |
|------|-------|
| Form name | Ramlatech RFP |
| Form ID | mjgjbgwk |
| Endpoint | https://formspree.io/f/mjgjbgwk |
| Method | Native HTML POST |
| Required fields | Organization, contact name, email, project title, scope |
| Submissions sent to | kareem@ramlatech.com |

### Important Formspree Notes
- Free plan: 50 submissions/month per form
- If submission lands in Formspree spam: open it and click "Not Spam"
- To disable spam filter: Settings > Spam Protection > Formshield > Disable
- After submission: user redirected to thanks.html via _next hidden field
- Confirmation email to submitter: pending — requires paid plan or EmailJS

---

## 7. Booking — Google Calendar

| Item | Details |
|------|---------|
| Booking link | https://calendar.app.google/iimx72oQiLnDs8EJ9 |
| Type | Google Calendar appointment booking |
| Duration | 30 minutes |
| Implementation | Button opens link in new tab |
| Embed | Not possible — Google blocks iframe embedding |
| Upgrade option | Calendly free tier embeds properly |

---

## 8. Analytics — Google Analytics 4

| Item | Details |
|------|---------|
| Account | kareem@ramlatech.com Google account |
| Property name | Ramlatech |
| Measurement ID | G-KXS97MYKLJ |
| Dashboard | https://analytics.google.com |
| Status | Live and tracking |
| Implemented on | All 5 HTML pages |

### GA4 Script
```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-KXS97MYKLJ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-KXS97MYKLJ');
</script>
```

---

## 9. SEO

### Google Search Console
| Item | Details |
|------|---------|
| Account | kareem@ramlatech.com Google account |
| Property | https://ramlatech.com |
| Dashboard | https://search.google.com/search-console |
| Sitemap submitted | https://ramlatech.com/sitemap.xml |
| Status | Verified — processing data |

### Keyword Targeting
| Page | Primary Keyword | Secondary Keywords |
|------|----------------|-------------------|
| Home | boutique software agency | custom software development, software agency for businesses |
| Services | custom software development services | mobile app development agency, AI automation services |
| About | software agency founded in Palestine | technology built with purpose, boutique tech agency |
| Contact | hire a software agency | book software consultation, software development quote |

### Phase 1 SEO — Completed
- Meta titles and descriptions on all pages
- Open Graph tags on all pages
- Twitter/X card tags on all pages
- Structured data JSON-LD on home page
- sitemap.xml submitted to Google Search Console
- robots.txt configured
- Canonical URLs on all pages
- HTTPS enforced

### Phase 2 SEO — Completed
- Alt text on all images
- Unique H1 per page with target keywords
- Hero copy updated with full audience range
- Service section keyword intros on services.html
- Boutique software agency added naturally to about.html

### Phase 3 SEO — Pending
- Bing Webmaster Tools submission
- Agency directory listings (Clutch, GoodFirms, G2)
- Backlink building
- Blog content

---

## 10. Email Marketing — MailerLite

| Item | Details |
|------|---------|
| Account email | kareem@ramlatech.com |
| Dashboard | https://app.mailerlite.com |
| Plan | Free — up to 1,000 subscribers |
| Group | Blog Subscribers |
| Form name | Ramlatech Blog Newsletter |
| Form ID | 184727574659729402 |
| Subscribe endpoint | https://assets.mailerlite.com/jsonp/2267517/forms/184727574659729402/subscribe |
| Form preview | https://preview.mailerlite.io/forms/2267517/184727574659729402/share |
| Status | Live — embedded on all pages |
| Button color | #C4882B Gold |
| Button text | White #FFFFFF |

### Newsletter Implementation
| Placement | Location | Description |
|-----------|----------|-------------|
| Band | index.html above footer | Full-width navy section "Stay Rooted" — two-column, stacks on mobile |
| Footer | All pages (footer-brand column) | Compact inline form with → arrow button |

### Technical Notes
- Submission handled via `fetch()` with `mode: 'no-cors'` — fires to MailerLite, shows success state in-place
- MailerLite webforms script loaded before `</body>` on all pages: `groot.mailerlite.com/js/w/webforms.min.js`
- Double opt-in triggered by MailerLite after submission
- Success message replaces form in-place without page reload
- Hidden fields required: `ml-submit=1`, `anticsrf=true`
- Email field name: `fields[email]`
- Accessible: `sr-only` labels, `aria-label` on inputs, gold focus ring

---

## 11. Client Logo Carousel

Auto-scrolling strip of client logos displayed on all four main pages.

### Placement
| Page | Position |
|------|----------|
| index.html | Below services ticker, above "What We Build" section |
| about.html | Below page hero |
| services.html | Below page hero, above services nav |
| contact.html | Below page hero |

### Design Specs
| Property | Value |
|----------|-------|
| Background | `#0E1F38` (dark navy) |
| Border | `1px solid rgba(255,255,255,0.06)` top and bottom |
| Padding | `1.5rem 0` |
| Card size | `220×110px` |
| Card style | White `#fff`, `border-radius: 12px`, `padding: 0.75rem` |
| Card opacity | `0.85` default, `1.0` on hover |
| Hover effect | `opacity: 1` + `translateY(-2px)` |
| Animation | `logoScroll` — CSS `@keyframes`, 40s linear infinite |
| Loop method | 15 logos duplicated (30 total) — translate -50% for seamless loop |
| Images | `<img>` tags, `object-fit: contain`, `max-width/max-height: 100%` |

### Assets
All SVGs stored in `assets/clients/` — 15 files (Paltel, Jawwal, Reach, Palestinian Authority, PCBS, MTIT, PMA, World Bank, Bank of Palestine, Fine HH, NFPC, AlQuds Pharma, GIZ, Munib & Angela Masri, Upliftt).

Source: `ACT+ Customer Logos Updated/Large/` folder on Desktop. Each SVG was post-processed:
- `viewBox` tightened to clip-path bounds (or image-transform bounds where no clip-path existed)
- White slide-background `<rect>` elements removed
- `width`/`height` set to `100%` for fluid scaling

---

## 12. Google Business Profile

| Item | Details |
|------|---------|
| Account | kareem@ramlatech.com Google account |
| Business name | Ramlatech |
| Category | Software Company / Software Development Service |
| Website | https://ramlatech.com |
| Service areas | Palestine, Jordan, Iraq, UAE, Saudi Arabia, Qatar, Kuwait, Bahrain, Oman, United States, Canada |
| Booking URL | https://ramlatech.com/contact.html#book |
| Inquiry URL | https://ramlatech.com/contact.html |
| Confirmation URL | https://ramlatech.com/thanks.html |
| Status | Created and verified |

---

## 12. Google Ads

| Item | Details |
|------|---------|
| Account | kareem@ramlatech.com Google account |
| Campaign type | Search |
| Credit | $250 free credit |
| Target locations | UAE, Saudi Arabia, Qatar, Kuwait, Bahrain, Oman, Jordan, United States, Canada, United Kingdom |
| Excluded location | Palestine |
| Phone | 163-875-2915 |
| Status | Campaign set up — monitoring required |

---

## 13. Clutch.co

| Item | Details |
|------|---------|
| Account email | kareem@ramlatech.com |
| Status | Profile created — pending completion |

---

## 14. Social Media

| Platform | URL | Handle |
|----------|-----|--------|
| LinkedIn | https://www.linkedin.com/company/ramlatech | @ramlatech |
| X Twitter | https://x.com/ramlatech | @ramlatech |
| Instagram | https://www.instagram.com/ramlatech | @ramlatech |

---

## 15. Domain & DNS

| Item | Details |
|------|---------|
| Domain | ramlatech.com |
| Connected to | GitHub Pages |
| HTTPS | Enforced |
| CNAME file | Contains: ramlatech.com |

### DNS Records
| Type | Name | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | kareem499.github.io |

---

## 16. Content Marketing Roadmap

### Blog Posts Planned
| # | Title | Target Keyword | Audience | CTA |
|---|-------|---------------|----------|-----|
| 1 | What is an MVP? How to build one and get to market fast | what is an MVP | Startup founders | Book free consultation to scope MVP |
| 2 | How to choose a software agency — 10 questions to ask | how to choose a software agency | Businesses comparing agencies | Book free consultation |
| 3 | AI automation for SMEs — where to start and what to expect | AI automation small business | SMEs exploring AI | Book free AI consultation |
| 4 | How much does custom software development cost in 2026? | custom software development cost | Businesses budgeting for software | Get a free quote |

### Content Flywheel Per Post
```
Blog post (SEO)
    → YouTube video (long form)
    → Instagram Reel (60s)
    → LinkedIn article
    → Carousel (key takeaways)
    → WhatsApp/Stories
```

---

## 17. AI Search Optimization Roadmap

To appear in ChatGPT, Perplexity, Claude, and other AI searches:

- [ ] Submit to Bing Webmaster Tools (ChatGPT uses Bing index)
- [ ] Get listed on Clutch, GoodFirms, G2
- [ ] Build backlinks from tech publications
- [ ] Consistent NAP across all directories
- [ ] PR mentions in tech publications
- [ ] Answer questions on Quora and Reddit as Ramlatech
- [ ] Structured data already implemented

---

## 18. Pending Tasks

### High Priority
- [x] Embed MailerLite newsletter form — live on all pages (band + footer)
- [x] Add client logo carousel — all 4 pages (index, about, services, contact)
- [ ] Build blog.html
- [ ] Write Blog Post 1 — MVP guide
- [ ] Fix Google Search Console sitemap Couldn't fetch (check after 24h)
- [ ] Add confirmation email to form submitters

### Medium Priority
- [ ] Submit to Bing Webmaster Tools
- [ ] Complete Clutch.co profile
- [ ] Phase 3 SEO — agency directories
- [ ] Monitor and optimize Google Ads
- [ ] Image compression for page speed

### Future
- [ ] Blog content calendar execution
- [ ] Video content production
- [ ] Social media content calendar
- [ ] Case studies page
- [ ] Make GitHub repo public
- [ ] Google Business Profile — collect reviews
- [ ] AI Search Optimization execution

---

## 19. Key Decisions

| Decision | Reason |
|----------|--------|
| Personal GitHub Kareem499 | Contribution history shows on personal profile — better for portfolio |
| Plain HTML no framework | No build step, deploy anywhere, fast loading |
| GitHub Pages | Free, reliable, auto-deploys on push |
| Formspree HTML POST | Most reliable, no JavaScript conflicts |
| Calendar button not embed | Google blocks iframe embedding |
| MailerLite over Mailchimp | Better free tier — 1,000 subs vs 500 |

---

## 20. Contacts

| Role | Name | Email |
|------|------|-------|
| Owner and Developer | Kareem AlWazir | kareem@ramlatech.com |
| Personal email | Kareem AlWazir | kareamelwazir@gmail.com |
| Business email | Ramlatech | hello@ramlatech.com |
| GitHub | Kareem499 | https://github.com/Kareem499 |

---

Update this document whenever a new tool, integration, or decision is added to the project.
