// Shared TypeScript interfaces for the LUT database

export interface LutFile {
  name: string;
  type: string;
  size: number;
  sha256: string;
  format?: string;
  lut_3d_size?: number | null;
  domain_min?: [number, number, number] | null;
  domain_max?: [number, number, number] | null;
  generator?: string | null;
  copyright?: string | null;
  title?: string | null;
  variant?: string;
  original_filename?: string;
  public_path: string;
}

export interface LutInternal {
  title: string | null;
  generator: string | null;
  copyright: string | null;
  color_profile?: string | null;
}

export interface LutAuthor {
  name_zh: string;
  name_en: string;
  slug: string;
}

export interface LutEntry {
  id: string;
  name_zh: string;
  author: LutAuthor;
  category: string;
  category_zh: string;
  description: string;
  tags: string[];
  format: string;
  lut_3d_size: number | null;
  domain_min?: [number, number, number] | null;
  domain_max?: [number, number, number] | null;
  photo_style?: string | null;
  internal: LutInternal;
  total_size: number;
  files: LutFile[];
  preview_image: string;
  preview_images?: Array<{
    variant: string;
    path: string;
    source_url?: string;
    status?: string;
  }>;
  official_name?: string;
  display_name?: string;
  official_descriptions?: string[];
  display_description?: string;
  canonical_id?: string;
  source_items?: Array<{
    remote_item_id: number;
    source_page: string;
    download_url: string;
    preview_url: string;
  }>;
}

export interface CategoryMeta {
  id: string;
  name_zh: string;
  name_en: string;
  lut_count: number;
}

export interface AuthorMeta {
  slug: string;
  name_zh: string;
  name_en: string;
  lut_count: number;
}

export interface LutDatabase {
  meta: {
    updated: string;
    total_luts: number;
    total_files: number;
    source: string;
    official_card_count?: number;
    merged_duplicate_card_count?: number;
  };
  categories: CategoryMeta[];
  authors: AuthorMeta[];
  tags: string[];
  generators: string[];
  lut_3d_sizes: number[];
  formats: string[];
  luts: LutEntry[];
}
