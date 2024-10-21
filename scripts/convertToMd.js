const fs = require('fs').promises;
const path = require('path');

const sourceDir = path.join(__dirname, '..', 'text-articles');
const targetDir = path.join(__dirname, '..', 'src', 'content', 'articles');

async function convertToMd() {
  try {
    const files = await fs.readdir(sourceDir);
    
    for (const file of files) {
      if (path.extname(file) === '.txt') {
        const filePath = path.join(sourceDir, file);
        const content = await fs.readFile(filePath, 'utf-8');
        
        const title = path.basename(file, '.txt');
        const date = new Date().toISOString().split('T')[0];
        
        const mdContent = `---
title: "${title}"
author: "Auto Generated"
date: ${date}
image: "https://via.placeholder.com/800x400.png?text=${encodeURIComponent(title)}"
excerpt: "${content.slice(0, 150)}..."
category: "Uncategorized"
---

${content}`;

        const mdFilePath = path.join(targetDir, `${title}.md`);
        await fs.writeFile(mdFilePath, mdContent);
        
        console.log(`Converted ${file} to Markdown`);
      }
    }
    
    console.log('Conversion complete!');
  } catch (error) {
    console.error('Error during conversion:', error);
  }
}

convertToMd();