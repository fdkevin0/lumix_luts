import type { LutDatabase, LutEntry, CategoryMeta, AuthorMeta } from '../types/lut';
// The canonical database is generated from an immutable official snapshot.
import lutData from '../../data/canonical/luts.json';

const db = lutData as unknown as LutDatabase;

export function getAllLuts(): LutEntry[] {
  return db.luts;
}

export function getLutBySlug(slug: string): LutEntry | undefined {
  return db.luts.find((lut) => lut.id === slug);
}

export function getAllSlugs(): string[] {
  return db.luts.map((lut) => lut.id);
}

export function getCategories(): CategoryMeta[] {
  return db.categories;
}

export function getAuthors(): AuthorMeta[] {
  return db.authors;
}

export function getAllTags(): string[] {
  return db.tags;
}

export function getGenerators(): string[] {
  return db.generators;
}

export function getLut3dSizes(): number[] {
  return db.lut_3d_sizes;
}

export function getFormats(): string[] {
  return db.formats;
}

export function getMeta() {
  return db.meta;
}

export function getCategoryByLut(lut: LutEntry): CategoryMeta | undefined {
  return db.categories.find((c) => c.id === lut.category);
}
