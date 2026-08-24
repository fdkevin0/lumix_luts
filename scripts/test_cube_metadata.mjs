import { readFile } from 'node:fs/promises';
import { buildDownloadTitle, rewriteCubeMetadata } from '../src/lib/cube-metadata.ts';

const source = await readFile(
  'data/canonical/luts/anniversary/desong/millennium-echo-cold/anniversary--desong--millennium-echo-cold--default.cube',
  'utf8',
);
const output = rewriteCubeMetadata(source, {
  title: '千禧回声 Cold',
  photoStyle: 'STD',
  advanced: { GRAINEFFECT: 'LOW', SHARPNESS: -1.5, NOISEREDUCTION: 'L40' },
  customComments: '#LUMIXCONTRAST 2',
});
const rows = (value) => value
  .split(/\r?\n/)
  .filter((line) => /^[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+$/.test(line.trim()));

if (rows(source).length !== rows(output).length) throw new Error('LUT 数据行数发生变化');
if (!output.includes('TITLE "千禧回声 Cold"')) throw new Error('TITLE 未写入');
if (!output.includes('#LUMIXPHOTOSTYLE STD')) throw new Error('LUMIXPHOTOSTYLE 未写入');
if (!output.includes('#GRAINEFFECT LOW') || !output.includes('#SHARPNESS -1.5') || !output.includes('#NOISEREDUCTION L40')) {
  throw new Error('高级 LUMIX 参数未写入');
}
if (!output.includes('#LUMIXCONTRAST 2')) throw new Error('实验性自定义注释未写入');
if (!output.includes('TITLE "千禧回声 Cold"\n#LUMIXPHOTOSTYLE STD\n#GRAINEFFECT LOW')) {
  throw new Error('LUMIX 元数据没有紧跟 TITLE');
}
const withExistingAdvanced = source.replace('LUT_3D_SIZE', '#GRAINEFFECT HIGH\nLUT_3D_SIZE');
const preservedAdvanced = rewriteCubeMetadata(withExistingAdvanced, { title: 'Keep', photoStyle: 'STD' });
if (!preservedAdvanced.includes('#GRAINEFFECT HIGH')) throw new Error('原文件官方画质参数未保留');
const overriddenAdvanced = rewriteCubeMetadata(withExistingAdvanced, {
  title: 'Override',
  photoStyle: 'STD',
  advanced: { GRAINEFFECT: 'LOW' },
});
if ((overriddenAdvanced.match(/#GRAINEFFECT/g) ?? []).length !== 1 || !overriddenAdvanced.includes('#GRAINEFFECT LOW')) {
  throw new Error('官方画质参数没有被唯一覆盖');
}
for (const [options, expectedMessage] of [
  [{ title: 'Bad', photoStyle: 'STD', advanced: { SHARPNESS: 5.5 } }, '非 V-Log 范围未校验'],
  [{ title: 'Bad', photoStyle: 'VLOG', advanced: { SHARPNESS: -0.5 } }, 'V-Log 范围未校验'],
  [{ title: 'Bad', photoStyle: 'STD', customComments: '#SHARPNESS 1' }, '自定义注释覆盖官方字段未拦截'],
]) {
  let rejected = false;
  try {
    rewriteCubeMetadata(source, options);
  } catch {
    rejected = true;
  }
  if (!rejected) throw new Error(expectedMessage);
}
console.log(`Cube metadata test passed; preserved ${rows(output).length} LUT rows.`);
if (buildDownloadTitle('千禧回声 Cold', 'cold') !== '千禧回声 Cold') {
  throw new Error('已包含变体的 TITLE 被重复追加');
}

const database = JSON.parse(await readFile('data/canonical/luts.json', 'utf8'));
let tested = 0;
for (const lut of database.luts) {
  for (const file of lut.files.filter((item) => item.type === 'cube')) {
    const input = await readFile(`data/${file.public_path}`, 'utf8');
    const title = buildDownloadTitle(lut.display_name ?? lut.name_zh, file.variant);
    const rewritten = rewriteCubeMetadata(input, {
      title,
      photoStyle: lut.base_photo_style.profile_tag,
    });
    if (rows(input).join('\n') !== rows(rewritten).join('\n')) {
      throw new Error(`${lut.id}: LUT 数据内容发生变化`);
    }
    if (!rewritten.includes(`TITLE "${title}"`)) {
      throw new Error(`${lut.id}: TITLE 错误`);
    }
    if (!rewritten.includes(`#LUMIXPHOTOSTYLE ${lut.base_photo_style.profile_tag}`)) {
      throw new Error(`${lut.id}: LUMIXPHOTOSTYLE 错误`);
    }
    tested += 1;
  }
}
console.log(`Validated downloadable metadata for ${tested} .cube files.`);
