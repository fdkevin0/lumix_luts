# Lumix LUTs / Lumix 色彩预设

Panasonic Lumix 相机 Real Time LUT .cube 色彩预设合集，可通过 [LUMIX Lab](https://panasonic.jp/support/global/cs/dsc/lumix_lab/) 应用或 SD 卡导入相机。

## 目录结构 / Directory Structure

```
luts/
  <合集名>/
    <作者名>/
      *.cube        # LUT 文件
      meta.yaml     # 元数据
scripts/
  validate.py       # 验证 cube 文件格式和 meta.yaml 一致性
  build-site.py     # 生成静态下载网站
site/               # 静态网站文件
```

## .cube 文件格式 / Cube File Format

Lumix 相机仅支持 `.cube` 格式的 LUT 文件，要求：

- **LUT_3D_SIZE 33**：33×33×33 数据点（35937 行数据）
- **#LUMIXPHOTOSTYLE 标签**：必须在文件 header 中声明基础 Photo Style
- **UTF-8 编码**：无 BOM
- 文件名规范：`<名称>_base_<PHOTOSTYLE>.cube`

### Photo Style 标签对照表

| 标签 | Photo Style |
|------|------------|
| `STD` | Standard |
| `VIVD` | Vivid |
| `NAT` | Natural |
| `LCLASN` | L.ClassicNeo |
| `FLAT` | Flat |
| `LAND` | Landscape |
| `PORT` | Portrait |
| `MONO` | Monochrome |
| `LMONO` | L.Monochrome |
| `LMONOD` | L.Monochrome D |
| `LMONOS` | L.Monochrome S |
| `LEICAMONO` | LEICA Monochrome |
| `CNED2` | Cinelike D2 |
| `CNEV2` | Cinelike V2 |
| `709L` | Like709 |
| `2100HLG` | Like2100(HLG) |
| `2100HLGF` | Like2100(HLG) Full Range |
| `VLOG` | V-Log |

缺少标签时相机默认使用 V-Log 作为基础 Photo Style。相机最多注册 39 个 LUT 文件。

### 示例 .cube 文件头部

```
# Created by Author Name
#LUMIXPHOTOSTYLE STD

LUT_3D_SIZE 33
DOMAIN_MIN 0.0 0.0 0.0
DOMAIN_MAX 1.0 1.0 1.0
0.000000 0.000000 0.000000
...
```

## 如何添加新 LUT / Adding New LUTs

1. 将 `.cube` 文件放入 `luts/<合集>/<作者>/` 目录
2. 在同目录创建或编辑 `meta.yaml`，添加 LUT 条目
3. 运行 `python scripts/validate.py` 验证
4. 运行 `python scripts/build-site.py` 更新网站
5. 提交并推送

## 工具依赖 / Tool Dependencies

- Python 3.10+
- PyYAML：`pip install pyyaml`

## License

各 LUT 文件的版权归其原作者所有。

## Cloudflare Workers 部署

网站以 Astro 静态站点部署到 Cloudflare Workers Static Assets，生产域名为
`https://lumix.fdkevin.cloud`。Wrangler 配置位于 `wrangler.jsonc`，构建产物目录为
`dist/`；Custom Domain 会在部署时由 Cloudflare 自动管理 DNS 和证书。

手动部署：

```bash
npm run build
npx wrangler deploy
```

本地预览 Workers Static Assets 构建结果：

```bash
npm run cf:dev
```

自动部署使用 Cloudflare Dashboard 的 Git 绑定。当前 Worker 已创建，因此进入
**Workers & Pages → lumix-luts → Settings → Builds → Connect**，选择本仓库并使用
以下构建设置：

- Production branch：`main`
- Build command：`npm run build`
- Deploy command：`npx wrangler deploy`
- Root directory：仓库根目录（留空）

GitHub Actions 仅执行数据校验和 Astro 构建，不负责部署，也不需要 Cloudflare
secrets。

## Canonical 数据与审计流程

当前网站使用 `data/canonical/luts.json`，而不是直接使用旧版的 `luts/luts.json`。
规范化资源位于 `data/canonical/`，官方页面和下载包按日期保存于
`data/snapshots/<YYYY-MM-DD>/`。原有 `luts/` 目录保留作为兼容和恢复来源，不会被自动删除。

```text
data/
  snapshots/<date>/       # 官方 HTML、原始 zip/rar、快照 manifest
  canonical/
    luts/                 # Linux 安全的规范文件名
    previews/             # 网站展示预览
    manifests/            # 每个 LUT 的来源、变体、哈希和文件清单
    luts.json             # Astro 网站数据库
  camera/aliases.json     # 相机导入短别名
  review/pending.json      # 待人工确认项目
```

重新生成规范数据前，必须先准备完整的官方四分类快照，然后运行：

```bash
npm run audit:canonical
npm run validate:canonical
npm run build
```

审计流程不会自动删除或覆盖旧快照。遇到无法唯一匹配、变体无法判断、哈希异常或压缩包缺失时会停止；异常内容进入人工确认流程后才能进入 canonical 数据。
