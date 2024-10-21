import { defineCollection, z } from 'astro:content';

const articlesCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    author: z.string(),
    date: z.date(),
    image: z.string(),
    excerpt: z.string(),
    category: z.string(),
    subcategory: z.string().optional(),
  }),
});

export const collections = {
  articles: articlesCollection,
};