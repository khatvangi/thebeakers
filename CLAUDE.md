# The Beakers

STEM research rewritten for undergraduate students. Cutting-edge research translated into language students can understand, connected to what they're learning in class.

**Live site:** https://thebeakers.com

## Vision

- Research papers rewritten for undergraduates with curriculum connections
- Show students how their coursework applies to real research
- Difficulty levels: Freshman, Sophomore, Junior+
- No AI slop, no clickbait, academic honesty

**Motto:** व्यये कृते वर्धत एव नित्यं — "Knowledge always grows when shared" (Chanakya Niti)

## Site Structure

```
thebeakers.com/
├── index.html          # Main page with cards, animations, newsletter
├── index-v1.html       # Backup: Original dark theme with tags
├── index-v2.html       # Backup: Light cream theme with cards
├── logo.png            # Main logo (transparent)
├── logo-48.png         # Header logo
├── favicon.ico         # Browser favicon
├── [discipline].png    # Card images (biology, chemistry, physics, etc.)
└── [discipline].html   # Category pages (coming soon)
```

## Disciplines (Card Categories)

### Natural Sciences
- Biology - biology.png
- Chemistry - chemistry.png
- Physics - physics.png
- Agriculture - agriculture.png

### Technology
- Artificial Intelligence - ai.png

### Engineering
- Engineering (Civil, Mechanical, Electrical, Chemical) - engineering.png

### Mathematics
- Mathematics - mathematics.png

## Design

### Theme
- Dark background (#0f172a)
- Card-based layout with Midjourney illustrations
- Plus Jakarta Sans + Instrument Serif fonts
- Inspired by writingexamples.com (Webby award winner)

### Animations
- Hero text slide-up on load
- Motto fade-in with delay
- Cards fade-in on scroll (staggered via Intersection Observer)
- Card image zoom on hover
- Swoosh animation around newsletter form
- Smooth scroll navigation

### Color Palette
```css
--bg-dark: #0f172a
--bg-card: #1e293b
--accent-green: #10b981  (Natural Sciences)
--accent-blue: #3b82f6   (Technology)
--accent-orange: #f59e0b (Engineering)
--accent-purple: #8b5cf6 (Mathematics)
```

## Sections

1. **Hero** - Title, tagline, Chanakya quote
2. **Disciplines** - 7 cards with category images
3. **Beyond Articles** - Podcasts & Curated Videos
   - Weekly Podcasts: This Week in Chemistry/Engineering/Biology/Math
   - Curated Videos: Lecture highlights, lab demos, concept explainers
4. **Newsletter** - Email signup with swoosh animation
5. **Footer** - Founding Editor, links

## Deployment

- **Hosting:** Cloudflare Pages
- **Repo:** https://github.com/khatvangi/thebeakers
- **Domain:** thebeakers.com (Cloudflare DNS)

## Related Sites

- **SPS Daily:** https://spsdaily.thebeakers.com — Science, Philosophy & Society digest
- **Course:** https://course.thebeakers.com — (placeholder)
- **Newsletter:** https://newsletter.thebeakers.com — Listmonk instance

## Planned Features

- [ ] Individual discipline pages with articles
- [ ] Weekly podcasts
- [ ] Curated YouTube video playlists
- [ ] Curriculum connections (course tags)
- [ ] Pop-up definitions
- [ ] Difficulty level badges

## Contact

- **Founding Editor:** Kiran Boggavarapu
- **Email:** thebeakerscom@gmail.com
