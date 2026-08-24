# CUBE SDK 与 LUMIX LUT 元数据调研

调研日期：2026-08-24
范围：可用于本项目（Astro/TypeScript 与构建期 Node 脚本）的 `.cube` 解析/写入方案，以及 Panasonic LUMIX Real Time LUT 的官方元数据。

## 结论摘要

1. **没有找到已验证、成熟且原生支持 LUMIX 扩展标签的 TypeScript CUBE SDK。** Adobe/IRIDAS CUBE 是文本格式，LUMIX 的 `#LUMIXPHOTOSTYLE` 与画质调整标签属于注释行扩展；最稳妥的实现是使用严格的 CUBE 解析/校验器，再由项目自己的 writer 在 `TITLE` 后插入白名单元数据。
2. **可直接使用的基础库**：
   - [`parse-cube-lut`](https://github.com/thibauts/parse-cube-lut)：MIT、Node/CommonJS，解析 Adobe CUBE 的标题、类型、尺寸、域和数据；仓库 README 明确定位为 parser（47 stars、2 commits），没有 writer，也不会保留任意注释扩展，因此不适合作为唯一的下载重写层。
   - [`cube-lut.js`](https://github.com/ssssota/cube-lut.js)：TypeScript 的 parser/generator，npm 资料显示版本 1.0.2；可作为候选，但应在引入前锁定版本并补充针对 LUMIX 注释、顺序、UTF-8 和 33³ 点数的项目测试。其公开资料没有声明 Panasonic 标签支持。
   - [`THREE.LUTCubeLoader`](https://threejs.org/docs/pages/LUTCubeLoader.html)：three.js 官方 addon，能把 CUBE 文本解析为 3D 数据纹理；定位是渲染加载器，不提供元数据 writer，不适合服务器端下载文件重写。
   - [`@azphalt/importer-cube`](https://www.npmjs.com/package/%40azphalt/importer-cube)：带 TypeScript declarations 的新包，可验证并封装 1D/3D CUBE，但其目标是 `.azp` 资产打包，且公开版本很新、无依赖用户，不能视为已成熟的 LUMIX writer。
3. **建议本项目不增加运行时依赖**：现有 Python 构建脚本已经能读取/校验 `.cube`。下载时复制 LUT 数据、重建规范化头部（`TITLE`、`#LUMIXPHOTOSTYLE`、可选官方画质标签）比依赖一个只支持标准 CUBE 头的库更可控；若以后迁移到 TypeScript，可优先评估 `cube-lut.js`，但仍需自有 metadata writer。

## Adobe/IRIDAS CUBE 基础约束

[Adobe Cube LUT Specification 1.0（[Adobe 原始 PDF 地址](https://wwwimages2.adobe.com/content/dam/acom/en/products/speedgrade/cc/pdfs/cube-lut-specification-1.0.pdf)，[可访问镜像](https://kono.phpage.fr/images/a/a1/Adobe-cube-lut-specification-1.0.pdf)）] 定义了 `TITLE`、`DOMAIN_MIN`/`DOMAIN_MAX`、`LUT_1D_SIZE` 或 `LUT_3D_SIZE` 等关键字及采样顺序。3D LUT 的 R 轴变化最快、B 轴最慢，`LUT_3D_SIZE N` 对应 `N³` 行 RGB 三元组（规格示例及参考实现见 PDF 第 14–16 页）。

因此下载重写器必须：

- 保留原始 LUT 数值与采样顺序，不做色彩变换；
- 校验 `LUT_3D_SIZE` 与实际行数一致（LUMIX Lab 官方创建的 LUT 为 33-grid）；
- 使用 UTF-8，并只把扩展信息放在数据开始前的注释行区域。

## Panasonic 官方 LUMIX 元数据

### 已确认：基础照片风格

Panasonic 的 [DC-S5M2 官方完整指南](https://eww.pavc.panasonic.co.jp/dscoi/DC-S5M2/html/DC-S5M2_DVQP2839_eng/0180.html)、[DC-S1M2ES 官方指南](https://eww.pavc.panasonic.co.jp/dscoi/DC-S1M2ES/html/DC-S1M2ES_DVQP3355_eng/0079.html) 和 [DC-GH7 官方指南](https://eww.pavc.panasonic.co.jp/dscoi/DC-GH7/html/DC-GH7_DVQP3109_eng/0075.html) 明确说明：自制 `.cube` 可在 `TITLE` 下方插入照片风格信息；`#LUMIXPHOTOSTYLE` 与标签之间必须是半角空格；缺失或错误时机身默认使用 V-Log。官方列表包含 `STD`、`VIVD`、`NAT`、`LCLASN`、`FLAT`、`LAND`、`PORT`、`MONO`、`LMONO`、`LMONOD`、`LMONOS`、`LEICAMONO`、`CNEA2`、`CNED2`、`CNEV2`、`709L`、`VLOG`、`STDHLG`/`MONOHLG`、`2100HLG`、`2100HLGF` 等，具体可按机型固件版本变化。

规范示例：

```text
TITLE "Official LUT Name"
#LUMIXPHOTOSTYLE PORT
LUT_3D_SIZE 33
```

### 已确认：官方画质调整标签（不是用户消息中的 `#LUMIXCONTRAST` 等）

Panasonic [DC-L10 官方指南的 LUT Library 页面](https://eww.pavc.panasonic.co.jp/dscoi/DC-L10/html/DC-L10_DVQP3497_eng/0077.html) 明确记录了可写入 LUT 的画质调整信息，并给出标签与取值映射：

| 画质项 | 官方标签 | 官方值示例 |
| --- | --- | --- |
| Grain Effect | `#GRAINEFFECT` | `OFF`、`LOW`、`STD`、`HIGH`（LUMIX Lab 侧为 `L0`–`L100` 区间） |
| Color Noise | `#COLORNOISE` | `OFF`、`ON`（LUMIX Lab 侧为 `L0`/`L1`） |
| Sharpness | `#SHARPNESS` | 相机 −5…+5；LUMIX Lab 侧使用 `L0`–`L100` 映射 |
| Noise Reduction | `#NOISEREDUCTION` | 与 Sharpness 类似的相机/LUMIX Lab 映射 |

该页面同时说明：标签与设置值之间必须有半角空格；没有 `#LUMIXPHOTOSTYLE` 时，画质调整信息不能加载；不同机型/照片风格可支持的项目不同。LUMIX Lab 的官方帮助页也确认启用“Add Image Qlty. Adj. Info”后会把画质调整信息写入 LUT，并在传输到相机时自动应用（[LUMIX Lab 官方帮助](https://av.jpn.support.panasonic.com/support/global/cs/soft/lumix_lab/en/cts/a1.html)）。

### 未验证：`#LUMIXCONTRAST`、`#LUMIXHIGHLIGHT`、`#LUMIXSHADOW`、`#LUMIXSATURATION`、`#LUMIXSHARPNESS`

在检索到的 Panasonic 官方指南、LUMIX Lab 官方帮助和 Adobe CUBE 规范中，没有找到上述 `#LUMIX...` 标签的定义或取值表。Panasonic 确实在相机菜单中提供 Contrast/Highlight/Shadow/Saturation 等实时画质调节（例如 [DC-G9M2 官方指南](https://eww.pavc.panasonic.co.jp/dscoi/DC-G9M2/html/DC-G9M2_DVQP3010_eng/0163.html)），但菜单项目名称不等于 `.cube` 文件标签。因此当前不能把这些字符串宣称为官方支持格式或默认写入下载文件。

如果产品需要“自定义其他 LUMIX 参数”，建议分两层：

1. **官方白名单模式（默认）**：只允许 `LUMIXPHOTOSTYLE`、`GRAINEFFECT`、`COLORNOISE`、`SHARPNESS`、`NOISEREDUCTION`，并按机型/固件校验枚举和数值范围。
2. **专家原始注释模式（显式确认）**：允许用户输入额外 `#KEY VALUE` 注释，但在 UI 和 manifest 中标记为 `unverified`，不保证相机识别，不覆盖官方字段，也不把它们称作 Panasonic 参数。

## 对下载功能的实现建议

- `TITLE` 使用官方 LUT 名称（ASCII 安全字符可用于文件名，显示名称可保留中文）；不要把来源、作者等 JSON 字段塞进 `TITLE`。
- 在 `TITLE` 后固定写入一个规范化的 `#LUMIXPHOTOSTYLE <tag>`；优先使用已从原始 `.cube` 读取的标签，其次使用人工确认/预览图记录；完全不确定时暂停人工审核，不猜测。
- 官方画质标签按原始文件是否存在、用户是否勾选“写入相机画质调整”分别处理；默认不凭图片推断这些值。
- 写出后重新解析并验证：UTF-8、唯一 `TITLE`、唯一 `LUT_3D_SIZE`、正确 `N³` 数据行、所有数值可解析且顺序未改变；同时保存原始 SHA-256、导出 SHA-256 与注入参数，便于追溯。
- 下载文件名遵循当前项目的 ASCII/Linux 规则；如需直接从 FAT32 卡导入，另提供不超过 8 个 ASCII 字符的兼容别名，因为 Panasonic 指南对 FAT32 文件名有 8 字符限制（[DC-L10 官方指南](https://eww.pavc.panasonic.co.jp/dscoi/DC-L10/html/DC-L10_DVQP3497_eng/0077.html)）。

## 风险与最终判断

标准 CUBE 解析库可以减少格式解析错误，但**不能替代 LUMIX 元数据层**。目前最可靠、可审计的方案是项目自有的“解析—白名单注入—再解析校验”流水线；第三方库仅作为标准 CUBE 数值校验或未来 TypeScript 迁移的候选，不应让其静默重排 LUT 数据或丢失 Panasonic 注释。
