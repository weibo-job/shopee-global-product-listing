# Shopee Global Product Listing Skill

一个用于 Codex 的 Shopee 跨境 Global Product 上架技能：从用户提供的拼多多授权商品页或商品素材出发，整理素材、生成英文商品资料、校验图片与 SKU，然后创建 Global Product 草稿并回读验证。

This skill prepares and verifies Shopee Global Product drafts from an authorized Pinduoduo product page or supplied product assets. It does not publish products to individual Shopee site shops.

## 能做什么

- 归档授权商品页中的主图、详情图、SKU 图和视频
- 将商品资料与图片整理为英文版上传包
- 保留源页可验证的标题、属性、价格、库存、兼容性和产品卖点
- 创建 Shopee Global Product、初始化 SKU 变体并回读验证
- 输出图片顺序、SKU 映射、库存、价格和无重复创建的验收证据

## 关键规则

1. 详情图必须先完成渲染页资产盘点、排除记录和 source-relative 顺序审查；清理后至少保留 6 张完整详情卡，最多选择 12 张，不能用推荐图、无关图或任意切片补数。
2. 同一商品包内所有英文详情图必须使用统一像素宽度，且每张都必须是独立完整的详情卡，不能把一张长图切成互相依赖的上下片段。
3. 源页能确认库存时使用源库存；源页无法确认时才使用默认库存 100，并明确记录 `stock_source=default_100`。
4. 价格按源 SKU 价格乘以 2，除非用户明确指定其他价格。
5. 只创建 Global Product，不发布到 MY、TH、TW、PH、VN、SG、MX、AR 等站点。
6. 不打印或提交 Partner Key、access token、refresh token、SSH 密钥或其他密钥。

## 安装

将此目录复制到 Codex 技能目录。该仓库已经内置素材打包、审计、授权、本地直连和 VPS helper 脚本，不需要另外安装 `shopee-listing-packager`：

```bash
cp -R shopee-global-product-listing "${CODEX_HOME:-$HOME/.codex}/skills/"
```

如果使用支持共享技能目录的其他 Codex 运行环境，也可以放到 `~/.agents/skills/`。

## 使用

直接提供一个拼多多授权商品链接，并说明要创建 Shopee Global Product。例如：

```text
使用 shopee-global-product-listing，把这个拼多多授权商品整理成英文 Shopee Global Product：<商品链接>
```

也可以提供已经下载的商品素材目录。技能会先归档和检查素材，再在 `${SHOPEE_LISTING_OUTPUT_DIR:-<cwd>/shopee-listing}/<product-folder>` 下分开保存 `原图/` 与 `英文版/`。

如果用户没有提供 SKU 库存，技能会使用 100 作为默认库存并在结果中标注；如果源页有库存，则不会用默认值覆盖源库存。

## 环境与依赖

- Python 3
- `agent-browser` 能力，用于授权商品页的完整渲染和懒加载扫描
- Shopee API 凭证和店铺/商户 OAuth 授权
- 默认使用用户自己配置的 VPS helper；也可以配置本地 Shopee API 直连
- 只有原图裁剪无法满足要求时，才需要带原图参考输入的 `imagegen` 能力

公共仓库不包含个人 VPS、商户、店铺、Token 或密钥。复制 `config.example.json` 到私有配置位置，或使用环境变量：

```bash
export SHOPEE_HELPER_BASE="https://your-helper.example.com"
export SHOPEE_PARTNER_ID="..."
export SHOPEE_PARTNER_KEY="..."
export SHOPEE_SHOP_ID="..."
export SHOPEE_MERCHANT_ID="..."
```

默认通道是用户配置的 VPS helper；未配置或 preflight 失败时必须停止报告，不得自动使用其他人的服务器。

安装后先运行：

```bash
python3 scripts/preflight.py
```

`enqueue_shopee_job.py` 默认只接受配置允许的商品包根目录。若你的工作区不同，可设置：

```bash
export SHOPEE_ALLOWED_ROOT="/path/to/your/Codex"
```

## 手动验证

```bash
python3 scripts/validate_listing_draft.py path/to/global_item_request.json
python3 scripts/scan_images.py path/to/package/原图/02_详情图 \
  --manifest-out path/to/package/原图/_evidence/manifest_详情图.json
python3 scripts/enqueue_shopee_job.py \
  --goods-id '<goods_id>' \
  --product-dir '/path/to/staged-product-package'
```

创建完成的验收标准包括：Global Product ID 非空、模型数量正确、SKU/价格/库存映射正确、详情图回读顺序与上传顺序一致、Shopee 错误字段为空，并且 `site_publish_called=false`。

## 目录说明

```text
SKILL.md                         # Codex 技能入口
agents/openai.yaml               # 技能在 Codex 中的显示信息
references/listing-rules.md      # 商品与图片规则
references/live-api-runbook.md  # helper/API 执行与故障处理
references/localization-audit-schema.md
scripts/scan_images.py           # 尺寸、比例、MD5 和顺序清单
scripts/make_package.py          # 原图/英文版目录初始化
scripts/long_canvas.py           # 分析用 long canvas 构建/切分
scripts/preflight.py             # 安装后环境/API 配置检查
scripts/validate_listing_draft.py
scripts/enqueue_shopee_job.py
```

## 安全提示

不要把商品授权链接中的私密参数、Shopee 凭据、SSH 私钥、helper 输出中的 token，或包含真实商品素材的本地工作目录提交到公开仓库。公开仓库只应包含本技能的说明、规则和通用脚本。

## License

MIT License，见仓库根目录的 `LICENSE`。
