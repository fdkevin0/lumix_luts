/**
 * Lossless metadata editor for Panasonic-compatible .cube files.
 *
 * It deliberately does not parse and re-serialize LUT samples: only the
 * textual header is replaced, so the original LUT payload remains byte-for-
 * byte unchanged. Panasonic documents require UTF-8 and place
 * #LUMIXPHOTOSTYLE directly below TITLE.
 */

export const LUMIX_PHOTO_STYLES = [
  ['STD', '标准'],
  ['VIVD', '生动'],
  ['NAT', '自然'],
  ['FLAT', '平直'],
  ['LAND', '风景'],
  ['PORT', '人物'],
  ['LCLAS', 'L.经典'],
  ['LCLASN', 'L.新经典'],
  ['LCLASG', 'L.经典金色'],
  ['MONO', '单色'],
  ['LMONO', 'L.单色'],
  ['LMONOD', 'L.单色 D'],
  ['LMONOS', 'L.单色 S'],
  ['LEICAMONO', 'LEICA 单色'],
  ['CNEA2', '电影感 A2'],
  ['CNED2', '电影感 D2'],
  ['CNEV2', '电影感 V2'],
  ['709L', 'Like709'],
  ['VLOG', 'V-Log'],
  ['HLG', 'HLG'],
  ['LOGC3', 'ARRI LogC3'],
  ['STDHLG', '标准 (HLG)'],
  ['MONOHLG', '单色 (HLG)'],
  ['2100HLG', '2100Like (HLG)'],
  ['2100HLGF', '2100Like (HLG) Full Range'],
] as const;

export const LUMIX_ADVANCED_PARAMS = [
  ['GRAINEFFECT', '颗粒效果'],
  ['COLORNOISE', '彩色噪点'],
  ['SHARPNESS', '锐度'],
  ['NOISEREDUCTION', '降噪'],
] as const;

const PHOTO_STYLE_SET = new Set<string>(LUMIX_PHOTO_STYLES.map(([tag]) => tag));
const ADVANCED_PARAM_SET = new Set<string>(LUMIX_ADVANCED_PARAMS.map(([key]) => key));
const TITLE_MAX_LENGTH = 128;

export type LumixPhotoStyle = (typeof LUMIX_PHOTO_STYLES)[number][0];
export type LumixAdvancedParam = (typeof LUMIX_ADVANCED_PARAMS)[number][0];
export type AdvancedValues = Partial<Record<LumixAdvancedParam, number | string>>;

export interface CubeMetadataOptions {
  title: string;
  photoStyle: string;
  advanced?: AdvancedValues;
  customComments?: string;
}

export function buildDownloadTitle(displayName: string, variant?: string | null): string {
  if (!variant || variant === 'default') return displayName;
  const label = `${variant.charAt(0).toUpperCase()}${variant.slice(1)}`;
  return displayName.toLowerCase().endsWith(` ${variant.toLowerCase()}`)
    ? displayName
    : `${displayName} ${label}`;
}

export function validatePhotoStyle(value: string): LumixPhotoStyle {
  const normalized = value.trim().toUpperCase();
  if (!PHOTO_STYLE_SET.has(normalized as LumixPhotoStyle)) {
    throw new Error(`不支持的 LUMIXPHOTOSTYLE：${value}`);
  }
  return normalized as LumixPhotoStyle;
}

function safeTitle(value: string): string {
  const title = value.trim().replace(/[\r\n\u0000]/g, ' ').replace(/"/g, "'");
  if (!title) throw new Error('TITLE 不能为空');
  if (title.length > TITLE_MAX_LENGTH) {
    throw new Error(`TITLE 不能超过 ${TITLE_MAX_LENGTH} 个字符`);
  }
  return title;
}

function lumixLabLevel(value: string, max = 100): string | null {
  const match = value.toUpperCase().match(/^L(\d{1,3})$/);
  if (!match) return null;
  const level = Number(match[1]);
  return Number.isInteger(level) && level >= 0 && level <= max ? `L${level}` : null;
}

function normalizedAdvanced(values: AdvancedValues = {}, photoStyle: LumixPhotoStyle): Array<[string, string]> {
  return Object.entries(values)
    .filter(([key, value]) => ADVANCED_PARAM_SET.has(key) && value !== '' && value != null)
    .map(([key, value]) => {
      const normalized = String(value).trim().toUpperCase();
      if (key === 'GRAINEFFECT') {
        const level = lumixLabLevel(normalized);
        if (!['OFF', 'LOW', 'STD', 'HIGH'].includes(normalized) && !level) {
          throw new Error('GRAINEFFECT 必须是 OFF、LOW、STD、HIGH 或 L0–L100');
        }
        return [key, level ?? normalized] as [string, string];
      }
      if (key === 'COLORNOISE') {
        const level = lumixLabLevel(normalized, 1);
        if (!['OFF', 'ON'].includes(normalized) && !level) {
          throw new Error('COLORNOISE 必须是 OFF、ON、L0 或 L1');
        }
        return [key, level ?? normalized] as [string, string];
      }
      const level = lumixLabLevel(normalized);
      if (level) return [key, level] as [string, string];
      const number = Number(normalized);
      const [min, max] = photoStyle === 'VLOG' ? [0, 10] : [-5, 5];
      if (!Number.isFinite(number) || number < min || number > max || number * 2 !== Math.round(number * 2)) {
        throw new Error(`${key} 在 ${photoStyle} 下必须为 ${min} 到 +${max}、步长 0.5，或 L0–L100`);
      }
      return [key, String(number)] as [string, string];
    });
}

interface CustomComment {
  key: string;
  line: string;
}

function normalizedCustomComments(value = ''): CustomComment[] {
  const lines = value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length > 16) throw new Error('实验性注释最多 16 行');
  const seen = new Set<string>();
  return lines.map((line) => {
    const match = line.match(/^#([A-Z][A-Z0-9_]{1,31})\s+([^\r\n]{1,128})$/i);
    if (!match) throw new Error(`实验性注释格式错误：${line}`);
    const key = match[1].toUpperCase();
    if (key === 'LUMIXPHOTOSTYLE' || ADVANCED_PARAM_SET.has(key)) {
      throw new Error(`${key} 是官方字段，请使用上方对应选项`);
    }
    if (seen.has(key)) throw new Error(`实验性注释字段重复：${key}`);
    seen.add(key);
    return { key, line: `#${key} ${match[2].trim()}` };
  });
}

function isTitle(line: string): boolean {
  return /^\s*TITLE\s+/i.test(line);
}

function isLumixMetadata(line: string): boolean {
  const match = line.trim().match(/^#([A-Z][A-Z0-9_]+)(?:\s+.*)?$/i);
  return Boolean(match && (match[1].toUpperCase() === 'LUMIXPHOTOSTYLE' || ADVANCED_PARAM_SET.has(match[1].toUpperCase())));
}

function lumixMetadataKey(line: string): string | null {
  const key = commentKey(line);
  return key && ADVANCED_PARAM_SET.has(key) ? key : null;
}

function commentKey(line: string): string | null {
  return line.trim().match(/^#([A-Z][A-Z0-9_]+)(?:\s+.*)?$/i)?.[1]?.toUpperCase() ?? null;
}

function validateCubePayload(lines: string[]): void {
  const sizeLine = lines.find((line) => /^\s*LUT_3D_SIZE\s+/i.test(line));
  const size = sizeLine ? Number(sizeLine.trim().split(/\s+/)[1]) : NaN;
  if (!Number.isInteger(size) || size < 2 || size > 256) {
    throw new Error('只支持有效的 3D .cube LUT');
  }
  let rows = 0;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#') || /^(TITLE|LUT_3D_SIZE|DOMAIN_MIN|DOMAIN_MAX)\b/i.test(trimmed)) continue;
    if (/^[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+$/.test(trimmed)) rows += 1;
  }
  if (rows !== size ** 3) {
    throw new Error(`LUT 数据行数异常：读取到 ${rows} 行，预期 ${size ** 3} 行`);
  }
}

export function rewriteCubeMetadata(text: string, options: CubeMetadataOptions): string {
  if (text.includes('\uFFFD')) throw new Error('LUT 不是有效的 UTF-8 文本');
  const newline = text.includes('\r\n') ? '\r\n' : '\n';
  const lines = text.replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n').split('\n');
  validateCubePayload(lines);
  const title = safeTitle(options.title);
  const photoStyle = validatePhotoStyle(options.photoStyle);
  const advanced = normalizedAdvanced(options.advanced, photoStyle);
  const advancedOverrides = new Map(advanced);
  const advancedKeys = new Set(advancedOverrides.keys());
  const existingAdvanced = new Map<string, string>();
  for (const line of lines) {
    const key = lumixMetadataKey(line);
    if (key && !advancedKeys.has(key) && !existingAdvanced.has(key)) {
      existingAdvanced.set(key, line.trim());
    }
  }
  const customComments = normalizedCustomComments(options.customComments);
  const customKeys = new Set(customComments.map(({ key }) => key));
  const kept = lines.filter((line) => !isTitle(line) && !isLumixMetadata(line) && !customKeys.has(commentKey(line) ?? ''));
  const sizeIndex = kept.findIndex((line) => /^\s*LUT_3D_SIZE\s+/i.test(line));
  const insertAt = sizeIndex === -1 ? 0 : sizeIndex;
  kept.splice(
    insertAt,
    0,
    `TITLE "${title}"`,
    `#LUMIXPHOTOSTYLE ${photoStyle}`,
    ...LUMIX_ADVANCED_PARAMS
      .map(([key]) => advancedOverrides.has(key)
        ? `#${key} ${advancedOverrides.get(key)}`
        : existingAdvanced.get(key))
      .filter((line): line is string => Boolean(line)),
    ...customComments.map(({ line }) => line),
  );
  return kept.join(newline).replace(/[\r\n]*$/, newline);
}

export function downloadText(text: string, filename: string): void {
  const blob = new Blob([text], { type: 'application/octet-stream;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function downloadCube(url: string, filename: string, options: CubeMetadataOptions): Promise<void> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`无法读取 LUT（HTTP ${response.status}）`);
  const text = await response.text();
  downloadText(rewriteCubeMetadata(text, options), filename);
}

export function attachLutDownloadHandlers(): void {
  document.addEventListener('click', async (event) => {
    const target = event.target instanceof Element ? event.target.closest<HTMLElement>('[data-lut-download]') : null;
    if (!target) return;
    event.preventDefault();
    await handleDownload(target, target.dataset);
  });
  document.addEventListener('submit', async (event) => {
    const form = event.target instanceof HTMLFormElement ? event.target.closest<HTMLFormElement>('[data-lut-download-form]') : null;
    if (!form) return;
    event.preventDefault();
    const values: AdvancedValues = {};
    form.querySelectorAll<HTMLInputElement | HTMLSelectElement>('[data-lumix-param]').forEach((input) => {
      if (input.value.trim()) values[input.dataset.lumixParam as LumixAdvancedParam] = input.value;
    });
    const title = form.elements.namedItem('title');
    const profile = form.elements.namedItem('profile');
    const button = form.querySelector<HTMLElement>('[data-lut-download-submit]');
    if (!button) return;
    await handleDownload(button, {
      ...form.dataset,
      ...button.dataset,
      title: title instanceof HTMLInputElement ? title.value : form.dataset.title,
      profile: profile instanceof HTMLSelectElement ? profile.value : form.dataset.profile,
      advanced: JSON.stringify(values),
      customComments: form.elements.namedItem('customComments') instanceof HTMLTextAreaElement
        ? (form.elements.namedItem('customComments') as HTMLTextAreaElement).value
        : '',
    });
  });
}

async function handleDownload(target: HTMLElement, data: DOMStringMap): Promise<void> {
  const originalText = target.textContent;
  target.setAttribute('aria-busy', 'true');
  target.textContent = '生成中…';
  try {
    const advanced = data.advanced ? JSON.parse(data.advanced) as AdvancedValues : {};
    await downloadCube(data.url ?? '', data.filename ?? 'lumix-lut.cube', {
      title: data.title ?? 'LUMIX LUT',
      photoStyle: data.profile ?? 'VLOG',
      advanced,
      customComments: data.customComments ?? '',
    });
  } catch (error) {
    window.alert(error instanceof Error ? error.message : 'LUT 下载失败');
  } finally {
    target.removeAttribute('aria-busy');
    target.textContent = originalText;
  }
}
