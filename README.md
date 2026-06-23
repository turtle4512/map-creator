# map-creator

map-creator 是一个给 Codex / agent 使用的城市导览地图工具包。它可以把城市、地点名或已有 POI JSON 转成可复查的 POI 数据，再用 OpenStreetMap / OSMnx 渲染 GIS 地图草稿，并可选用 GPT Image 做风格化海报。

## 项目结构

```text
map-creator/
|-- README.md                         # 项目说明
|-- SKILL.md                          # 给 Codex/agent 使用的操作说明
|-- config.example.json               # 配置模板，不放真实 key
|-- config.local.json                 # 本地真实配置，已被 .gitignore 忽略
|-- requirements.txt                  # Python 依赖
|-- guide_maps/
|   |-- cli/                          # 命令入口
|   |   |-- create_gis_map.py         # 主入口：城市/地点/POI JSON -> GIS 地图
|   |   |-- resolve_pois.py           # 只解析地点并保存 POI JSON
|   |   |-- style_poster_with_gpt_image.py
|   |   |-- run_full_map_pipeline.py
|   |   `-- validate_poi_alignment.py
|   |-- core/                         # 路径、配置、缓存、字体、通用工具
|   |-- geocoding/                    # 高德解析、坐标转换、POI 数据结构
|   |-- rendering/                    # OSM/GIS 地图渲染
|   |-- styling/                      # GPT Image 和本地风格预览
|   |-- examples/                     # 示例 POI 数据
|   `-- fonts/                        # 字体资源
|-- prompts/map_style_templates/      # GPT Image 风格化提示词模板
|-- tests/                            # 自动化测试
|-- cache/                            # 运行缓存，可删除
`-- outputs/                          # 运行输出，可删除
```

运行时常用输出目录：

```text
cache/
outputs/posters/
outputs/stylized/
outputs/poi_sets/
```

## 安装

```bash
python -m pip install -r requirements.txt
```

Windows PowerShell 如果中文输出仍然乱码，可以先设置：

```powershell
chcp 65001
$env:PYTHONIOENCODING="utf-8"
```

CLI 入口内部也会尽量把 stdout/stderr 设为 UTF-8。

## 配置

复制或编辑 `config.local.json`：

```json
{
  "amap": {
    "api_key": "你的高德地图 Web 服务 API Key",
    "timeout": 12
  },
  "gpt_image": {
    "api_key": "你的 OpenAI API Key",
    "model": "gpt-image-2",
    "endpoint": "https://api.openai.com/v1/images/edits",
    "template": "prompts/map_style_templates/01_手绘风城市导览地图.md",
    "output_dir": "outputs/stylized",
    "output_format": "png",
    "size": "1536x1024",
    "timeout": 120
  }
}
```

也可以用环境变量：

```powershell
$env:AMAP_KEY="你的高德 key"
$env:OPENAI_API_KEY="你的 OpenAI key"
```

运行目录可以用 `MAP_CREATOR_CACHE_DIR`、`MAP_CREATOR_OUTPUTS_DIR`、`MAP_CREATOR_POSTERS_DIR`、`MAP_CREATOR_STYLIZED_DIR`、`MAP_CREATOR_POI_SETS_DIR` 覆盖；旧的 `OPEN_GUIDE_MAPS_*` 变量仍然兼容。

`config.local.json` 已被 `.gitignore` 忽略，不要提交真实 key。`config.example.json` 只保留字段结构。

## 生成 GIS 地图

从城市和地点名生成地图：

```bash
python -m guide_maps.cli.create_gis_map --city 上海 --places "SLAB TOWN" "村口大树" "ALWAYS Coffee&Bar" --title "上海街区导览地图"
```

从已有 POI JSON 生成地图：

```bash
python -m guide_maps.cli.create_gis_map --city 上海 --poi-json guide_maps/examples/sample_pois.json --title "巨富长漫游指南"
```

解析地点并保存 POI JSON：

```bash
python -m guide_maps.cli.create_gis_map --city 南京 --places "地点1" "地点2" --title "南京小酒馆地图" --save-poi-json outputs/poi_sets/nanjing_bars.json
```

提示重点道路名，但不把它们当白名单：

```bash
python -m guide_maps.cli.create_gis_map --city 南京 --poi-json outputs/poi_sets/nanjing_bars.json --title "南京小酒馆地图" --road-labels 长江路 石鼓路 应天大街
```

关闭道路名：

```bash
python -m guide_maps.cli.create_gis_map --city 南京 --poi-json outputs/poi_sets/nanjing_bars.json --title "南京小酒馆地图" --no-road-labels
```

地图草稿输出到：

```text
outputs/posters/
```

## 只解析 POI

只解析地点并输出可复查的 POI JSON：

```bash
python -m guide_maps.cli.resolve_pois --city 南京 --names "地点1" "地点2" --output outputs/poi_sets/nanjing.json
```

POI JSON 会保留输入名、解析名、地址、区县、候选结果、置信度、GCJ-02 坐标和 WGS84 坐标。高德返回 GCJ-02，渲染前会转换为 WGS84 以匹配 OSMnx / OpenStreetMap。

## OSM 数据和速度

地图渲染需要访问 Overpass API。中国大陆网络访问 Overpass 可能很慢。

当前实现会：

- 单独请求一次路网 `graph_from_point()`。
- 把建筑、公园、水体、生活方式 POI、交通点等 `features_from_point()` 合并成一次请求，再在本地拆分图层。
- 使用 `cache/` 缓存 OSM 数据；同一区域再次生成会明显更快。

删除 `cache/` 后，下次生成会重新联网抓取 OSM 数据。

## GPT Image 风格化

把 GIS 草稿交给 GPT Image 风格化：

```bash
python -m guide_maps.cli.style_poster_with_gpt_image --input outputs/posters/<draft>.png
```

指定变量和模板：

```bash
python -m guide_maps.cli.style_poster_with_gpt_image --input outputs/posters/<draft>.png --vars outputs/stylized/prompt_dry_runs/vars.json --template prompts/map_style_templates/01_手绘风城市导览地图.md
```

没有 GPT Image key 时，GIS 草稿仍然可以正常生成。

## 测试

```bash
python -m compileall guide_maps tests
python -m pytest tests
```

如果 pytest 在系统临时目录没有权限，可以把临时目录放到项目内：

```powershell
$env:TMP="$PWD\.tmp"
$env:TEMP=$env:TMP
python -m pytest tests
```

当前测试覆盖 POI 解析、坐标转换、地图范围、道路名筛选、OSM feature 合并拆分、GPT Image 提示词和风格预览生成。

## 可删除目录

以下目录都是运行产物，可以删除后重新生成：

```text
cache/
outputs/
.pytest_cache/
__pycache__/
tests/__pycache__/
```
