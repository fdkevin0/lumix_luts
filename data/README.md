# LUT 数据管理

该目录把“官方原始证据”“规范化可用资源”和“网站生成数据”分开管理。

## 不变量

- `snapshots/` 中的历史文件不可原地覆盖或删除。
- canonical 文件名只使用小写 ASCII、数字和短横线。
- 文件名格式为 `<category>--<author>--<lut>--<variant>.<ext>`。
- 官方名称、作者原文、描述、下载地址、预览地址和原始文件名保存在 manifest 中。
- 同内容不同官方条目保留来源记录，通过 SHA-256 标记重复，不静默删除。
- 未知 Photo Style 保持未知，不默认写成 V-Log。
- 每张预览图左上角的“基于…”标注记录在 `canonical/preview-profiles.json`；`.cube` 中存在 `#LUMIXPHOTOSTYLE` 时优先读取，并与图片标注交叉校验。缺少该字段的 `.cube`/`.vlt` 会另外记录机身默认回退值 `VLOG`，不覆盖图片的原始基准标注。
- 任何无法唯一判断的字段都会阻止 canonical 更新并进入 `review/pending.json`。

## 2026-08-24 快照

- 官方卡片：57
- 官方 canonical LUT：57（千禧回声拆分为 Cold/Warm 两个条目）
- canonical LUT 文件：63
- “千禧回声”包含 `cold` 和 `warm` 两个变体
- 已知同内容组：`light-jp-blue` 与 `blue-ripple`

## 目录说明

- `snapshots/<date>/source-pages/`：四个官方分类页面 HTML。
- `snapshots/<date>/raw-archives/`：未经修改的官方 zip/rar。
- `snapshots/<date>/manifest.json`：页面和压缩包的 SHA-256。
- `canonical/manifests/`：逐 LUT provenance 和变体映射。
- `canonical/luts.json`：静态网站使用的数据。
- `canonical/preview-profiles.json`：预览图原文标注、标准 Photo Style 标签和中文名称。
- `camera/aliases.json`：S9、S5M2、S5M2X、G9M2、GH7 的独立短别名。
