# Ramlatech Website Roadmap

## Completed
- Nov 2026: manifesto share image `assets/og-manifesto.png` (1200×630) rendered from `assets/og-manifesto.html`
- Nov 2026: blog dashboard at /admin (write & schedule posts), Playgeko-style blog with categories, plus AI posts every 2 days incl. sourced comparisons (see DOCUMENTATION.md §18)
- Client logo carousel added to all 4 pages (index, about, services, contact) — 15 ACT+ client SVGs, auto-scrolling, dark navy strip
- Website launched on GitHub Pages
- Custom domain configured: ramlatech.com
- SSL/HTTPS enabled
- SEO meta tags, Open Graph, Twitter cards added to all pages
- sitemap.xml and robots.txt added
- Contact and RFP form success messages fixed
- Footer social links updated (LinkedIn, X, Instagram)
- Copyright year updated to 2026
- SVG icons replacing emojis across all pages
- Google Business Profile created and verified
- Google Ads campaign set up with $250 credit targeting GCC, USA, Canada, UK, and Jordan
- Google Analytics GA4 added to all pages (G-KXS97MYKLJ)
- sitemap.xml submitted to Google Search Console
- Cloudflare set up as DNS/CDN proxy with HSTS, Full SSL
- llms.txt created for AI search engine discovery
- robots.txt updated with explicit AI crawler allow rules
- Structured data (JSON-LD) added to about.html, services.html, blog.html
- Cloudflare email obfuscation disabled (resolved 11 broken link errors)
- Sitemap lastmod dates updated and resubmitted to Google Search Console
- Nov 2026: carousel logos converted to WebP (2.6 MB → ~340 KB), BMORE Jordan added, breadcrumbs/FAQ/services structured data, 1200×630 share card, thanks.html noindex, contact mobile overflow fixed

## Pending
- Create a GitHub fine-grained token and sign in at ramlatech.com/admin
- Add ANTHROPIC_API_KEY GitHub secret to start AI posts (then run the *Blog* workflow once with *Write an AI post now* and review it)
- Decide on duplicate logos: MTIT appears twice (old + new) on all pages; homepage also shows PMA twice
- After deploy: run Google Rich Results Test on contact.html (FAQ) and resubmit sitemap
- Monitor Google Ads performance
- Monitor Google Business Profile for reviews
- Respond to Google reviews promptly
- Email confirmation to form submitters (Web3Forms or similar)

## Future Roadmap
- Email confirmation sent to users after contact/RFP form submission
