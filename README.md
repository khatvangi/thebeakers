# Astro News Website

This project is a modern, responsive news website built with Astro, featuring dynamic content management and automatic article generation from text files.

## Features

- Built with Astro for fast, efficient static site generation
- Responsive design using Tailwind CSS
- Dynamic content management using Astro's content collections
- Automatic conversion of text files to Markdown articles
- Categorized news sections (Sciences, Applied Sciences, Humanities)
- Featured articles on the homepage
- Individual article pages with full content

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- npm (v6 or later)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/astro-news-website.git
   cd astro-news-website
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

4. Open your browser and visit `http://localhost:4321` to see the website.

## Usage

### Adding New Articles

1. Place your text files in the `text-articles` directory.
2. Run the conversion script:
   ```
   npm run convert
   ```
3. The script will automatically convert text files to Markdown and place them in `src/content/articles`.

### Customizing Content

- Edit Markdown files in `src/content/articles` to update article content.
- Modify category pages in `src/pages` to change section layouts and content.

### Building for Production

To create a production-ready build:

```
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

- `src/`: Source files
  - `components/`: Reusable Astro components
  - `content/`: Content collections (articles)
  - `layouts/`: Page layouts
  - `pages/`: Astro pages and routing
  - `utils/`: Utility functions
- `public/`: Static assets
- `scripts/`: Utility scripts (e.g., text to Markdown conversion)
- `text-articles/`: Source text files for articles

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.