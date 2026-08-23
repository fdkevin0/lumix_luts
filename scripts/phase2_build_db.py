#!/usr/bin/env python3
"""Phase 2: Build luts.json database — extract metadata, download previews."""

import os, re, json, hashlib, urllib.request, html as htmlmod
from pathlib import Path

BASE = Path("/Users/fdkevin/Workspace/lumix_luts/luts")
PREVIEW_DIR = BASE / "previews"
PREVIEW_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# ============================================================
# Catalog — full metadata for all 57 LUTs
# ============================================================
CATALOG = [
    {
        "cat": "anniversary",
        "auth_slug": "tu-xiaodai",
        "lut_slug": "txd-agfaphoto-lebox",
        "name_zh": "TXD AgfaPhoto LeBox",
        "author_zh": "兔小呆",
        "author_en": "Tu Xiaodai",
        "desc": "爱克发一次性胶片模拟。整体色调偏冷，带有轻微的青蓝倾向，尤其在高光和阴影处表现明显，能让画面显得干净、冷静。色彩倾向对蓝色和绿色的还原更突出，红色和橙色则相对柔和，整体呈现出一种褪色复古感。在自然光下肤色偏冷白，用闪光灯时会略微偏暖。对比度中等偏高，适合表现街头、城市的硬朗感。",
        "tags": ["film", "cold-tone", "retro", "street"],
    },
    {
        "cat": "anniversary",
        "auth_slug": "desong",
        "lut_slug": "millennium-echo",
        "name_zh": "千禧回声",
        "author_zh": "德松Desong",
        "author_en": "Desong",
        "desc": "以Lumix CCD相机的成像风格为灵感，提炼优化了其色彩特征并赋予画面独特的千禧年复古质感。通过压缩高光和阴影，呈现出对比度中等偏低的影调，同时模拟CCD带着些许高光溢出的早期数码特有的明快感。在光线充足的情况下表现最佳，在光线不足或开启闪光灯的情况下也能保证肤色白皙透红。提供warm和cold两种色温偏向的版本。",
        "tags": ["ccd", "retro", "y2k", "portrait"],
    },
    {
        "cat": "anniversary",
        "auth_slug": "desong",
        "lut_slug": "millennium-echo-v2",
        "name_zh": "千禧回声 v2",
        "author_zh": "德松Desong",
        "author_en": "Desong",
        "desc": "此预设以Lumix CCD相机的成像风格为灵感。在模仿CCD影调色调的同时不降低画质。通过压缩高光和阴影，呈现对比度中等偏低的影调。预设提供warm和cold两种色温偏向的版本。",
        "tags": ["ccd", "retro", "y2k", "high-quality"],
    },
    {
        "cat": "anniversary",
        "auth_slug": "plady",
        "lut_slug": "y2000",
        "name_zh": "y2000",
        "author_zh": "plady",
        "author_en": "Plady",
        "desc": "参考早期CCD数码相机的成像风格，整体色调偏青，并在高光中加入轻微暖色，使画面在保持清透感的同时带有自然的阳光温度。高光略带溢出，暗部适度压缩。特别适合阳光环境与黄昏时段的人像拍摄。",
        "tags": ["ccd", "cyan-tone", "warm-highlight", "portrait", "sunset"],
    },
    # === portrait ===
    {
        "cat": "portrait",
        "auth_slug": "guo-bin",
        "lut_slug": "snow-portrait",
        "name_zh": "雪天人像",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "适用雪天人像，整体色调清冷干净的同时又保证肤色透亮。",
        "tags": ["portrait", "snow", "cool-tone", "skin-tone"],
    },
    {
        "cat": "portrait",
        "auth_slug": "zhang-heng",
        "lut_slug": "healing-light",
        "name_zh": "治愈光影",
        "author_zh": "张恒",
        "author_en": "Zhang Heng",
        "desc": "如同一缕柔和的阳光，为影像带来温暖而宁静的色调。",
        "tags": ["portrait", "warm-tone", "soft", "healing"],
    },
    {
        "cat": "portrait",
        "auth_slug": "guo-bin",
        "lut_slug": "seaside-sunset",
        "name_zh": "海边夕阳",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "冷暖对比更大，在冷暖上做出了不同效果。",
        "tags": ["portrait", "sunset", "warm-cool", "seaside"],
    },
    {
        "cat": "portrait",
        "auth_slug": "xue-luyao",
        "lut_slug": "warm-cool-tone",
        "name_zh": "冷暖色调",
        "author_zh": "薛璐瑶",
        "author_en": "Xue Luyao",
        "desc": "对室内光源作出了冷暖不同色调，人物看着更加自然。",
        "tags": ["portrait", "warm-cool", "indoor", "natural"],
    },
    {
        "cat": "portrait",
        "auth_slug": "xue-luyao",
        "lut_slug": "teal-orange-tone",
        "name_zh": "青橙色调",
        "author_zh": "薛璐瑶",
        "author_en": "Xue Luyao",
        "desc": "多半用于夜景的拍摄，不同灯光下有适度的冷暖和色偏。",
        "tags": ["night", "teal-orange", "urban", "lighting"],
    },
    {
        "cat": "portrait",
        "auth_slug": "xue-luyao",
        "lut_slug": "high-low-contrast",
        "name_zh": "高低对比度",
        "author_zh": "薛璐瑶",
        "author_en": "Xue Luyao",
        "desc": "统一光比和室外早中晚不同的阳光色温。",
        "tags": ["contrast", "outdoor", "color-temperature", "balanced"],
    },
    {
        "cat": "portrait",
        "auth_slug": "bozi-booz",
        "lut_slug": "spring-portrait",
        "name_zh": "春意人像",
        "author_zh": "波子Booz",
        "author_en": "Bozi Booz",
        "desc": "影调柔和反差低，人物肤色友好，适合阴天拍摄呈现清冷。",
        "tags": ["portrait", "soft", "low-contrast", "overcast"],
    },
    {
        "cat": "portrait",
        "auth_slug": "bozi-booz",
        "lut_slug": "forest-green-cool",
        "name_zh": "森绿清冷",
        "author_zh": "波子Booz",
        "author_en": "Bozi Booz",
        "desc": "明显的黄绿倾向，肤色有单独优化，适合顺光拍摄场景。",
        "tags": ["portrait", "green", "yellow-green", "skin-tone", "front-light"],
    },
    {
        "cat": "portrait",
        "auth_slug": "jon-simo",
        "lut_slug": "gritty-cinema",
        "name_zh": "暮色",
        "author_zh": "Jon Simo",
        "author_en": "Jon Simo",
        "desc": "电影感调色LUT。",
        "tags": ["cinematic", "film", "moody"],
    },
    {
        "cat": "portrait",
        "auth_slug": "guo-bin",
        "lut_slug": "seaside-portrait",
        "name_zh": "海边人像",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "让海水以及绿色背景更偏青绿色，画面更加具有胶片感。",
        "tags": ["portrait", "seaside", "cyan-green", "film"],
    },
    {
        "cat": "portrait",
        "auth_slug": "guo-bin",
        "lut_slug": "aesthetic-portrait",
        "name_zh": "唯美人像",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "保证肤色透亮的同时，让黄色和绿色更有胶片氛围。",
        "tags": ["portrait", "aesthetic", "film", "skin-tone", "warm"],
    },
    {
        "cat": "portrait",
        "auth_slug": "hailuoke",
        "lut_slug": "tibet-warm-light",
        "name_zh": "藏区暖光",
        "author_zh": "海螺壳",
        "author_en": "Hailuoke",
        "desc": "整体偏暖，低对比，给人温暖柔和的视觉感受。",
        "tags": ["portrait", "warm-tone", "low-contrast", "tibet"],
    },
    {
        "cat": "portrait",
        "auth_slug": "ejay",
        "lut_slug": "japanese-cyan-tone",
        "name_zh": "日系青调",
        "author_zh": "EJAY",
        "author_en": "EJAY",
        "desc": "色彩偏青高短调为主，适合人像阴天。",
        "tags": ["portrait", "japanese-style", "cyan", "overcast"],
    },
    {
        "cat": "portrait",
        "auth_slug": "ejay",
        "lut_slug": "skin-tone-opt",
        "name_zh": "肤色优化",
        "author_zh": "EJAY",
        "author_en": "EJAY",
        "desc": "不改变其他色调，削弱红色溢出。",
        "tags": ["portrait", "skin-tone", "red-reduction"],
    },
    {
        "cat": "portrait",
        "auth_slug": "tu-xiaodai",
        "lut_slug": "txd-grainy-film",
        "name_zh": "TXD Grainy Film",
        "author_zh": "兔小呆",
        "author_en": "Tu Xiaodai",
        "desc": "对比较强，有着不错的胶片质感。",
        "tags": ["film", "high-contrast", "grain", "portrait"],
    },
    {
        "cat": "portrait",
        "auth_slug": "tu-xiaodai",
        "lut_slug": "light-jp-blue",
        "name_zh": "轻日系-蓝",
        "author_zh": "兔小呆",
        "author_en": "Tu Xiaodai",
        "desc": "轻日系微冷调，着重肤色的优化，适合于日常大部分场景的拍摄。",
        "tags": ["japanese-style", "cool-tone", "skin-tone", "daily"],
    },
    {
        "cat": "portrait",
        "auth_slug": "tu-xiaodai",
        "lut_slug": "warm-skin-tone",
        "name_zh": "暖白肤色",
        "author_zh": "兔小呆",
        "author_en": "Tu Xiaodai",
        "desc": "针对肤色进行优化，呈现为暖白色，可补充阴天面部失色。",
        "tags": ["portrait", "warm-white", "skin-tone", "overcast"],
    },
    {
        "cat": "portrait",
        "auth_slug": "tu-xiaodai",
        "lut_slug": "txd-rag-film-cned2",
        "name_zh": "TXD RaG Film CNED2",
        "author_zh": "兔小呆",
        "author_en": "Tu Xiaodai",
        "desc": "对肤色进行了一定优化，适合夏日日常扫街、花草和人像的拍摄。",
        "tags": ["film", "summer", "street", "portrait", "skin-tone"],
    },
    {
        "cat": "portrait",
        "auth_slug": "desong",
        "lut_slug": "vintage-summer",
        "name_zh": "复古夏日",
        "author_zh": "德松Desong",
        "author_en": "Desong",
        "desc": "绿色系胶片的影调色调为基础风格，突出对蓝、绿色彩的刻画，同时对红色、橙色也有非常生动的呈现。亮部暖调细腻，暗部偏蓝带洋红。",
        "tags": ["film", "summer", "green", "vintage", "portrait"],
    },
    {
        "cat": "portrait",
        "auth_slug": "desong",
        "lut_slug": "mosslight",
        "name_zh": "薄暮苔痕",
        "author_zh": "德松Desong",
        "author_en": "Desong",
        "desc": "以人像胶片的影调色调为基础风格，增加少量温暖的色彩偏向。在光线充足的情况下表现最佳，对比度适中。在光线不足的情况下保证肤色优先。",
        "tags": ["portrait", "film", "warm", "moss", "dusk"],
    },
    {
        "cat": "portrait",
        "auth_slug": "tu-xiaodai",
        "lut_slug": "txd-eterna",
        "name_zh": "TXD Eterna",
        "author_zh": "兔小呆",
        "author_en": "Tu Xiaodai",
        "desc": "基于STD调色，从徕卡Eternal滤镜中获得调色思路，改变了影调但保留了蓝紫的味道。整体色调偏重，比较吃光线。人像拍摄时一定要有光源。",
        "tags": ["film", "eterna", "purple-blue", "portrait", "lighting-critical"],
    },
    # === outdoor ===
    {
        "cat": "outdoor",
        "auth_slug": "ali-halip",
        "lut_slug": "summer",
        "name_zh": "夏日",
        "author_zh": "阿里Halip",
        "author_en": "Ali Halip",
        "desc": "使用时叠加Sample LUT2，透明度控制色彩亮度。",
        "tags": ["summer", "outdoor", "layered"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "ba-wenhuan",
        "lut_slug": "dark-tone-story",
        "name_zh": "暗调故事",
        "author_zh": "巴文欢",
        "author_en": "Ba Wenhuan",
        "desc": "基于2383风格，根据vlog曲线特性加以调整生成。",
        "tags": ["cinematic", "dark-tone", "vlog", "2383"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "ba-wenhuan",
        "lut_slug": "pink-youth",
        "name_zh": "粉黛青春",
        "author_zh": "巴文欢",
        "author_en": "Ba Wenhuan",
        "desc": "基于2383风格，根据vlog曲线特性加以调整生成。",
        "tags": ["cinematic", "pink", "youth", "vlog", "2383"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "ba-wenhuan",
        "lut_slug": "verdant-breath",
        "name_zh": "葱绿气息",
        "author_zh": "巴文欢",
        "author_en": "Ba Wenhuan",
        "desc": "由Portra800和Velvia胶片风格调整生成。",
        "tags": ["film", "green", "portra800", "velvia", "nature"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "plady",
        "lut_slug": "summer-breeze",
        "name_zh": "夏日暖风",
        "author_zh": "Plady",
        "author_en": "Plady",
        "desc": "具有低饱和度特性，类似留银冲洗的复古胶片味道。",
        "tags": ["film", "summer", "low-saturation", "retro", "bleach-bypass"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "plady",
        "lut_slug": "rich-tone",
        "name_zh": "浓厚格调",
        "author_zh": "Plady",
        "author_en": "Plady",
        "desc": "具有低饱和度特性，类似留银冲洗的复古胶片味道。",
        "tags": ["film", "rich", "low-saturation", "retro"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "plady",
        "lut_slug": "grey-cinema",
        "name_zh": "灰度电影",
        "author_zh": "Plady",
        "author_en": "Plady",
        "desc": "晴天时蓝天呈现高级银灰色，阴天街拍则散发清冷气息。",
        "tags": ["cinematic", "grey", "silver", "street", "overcast"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "bozi-booz",
        "lut_slug": "vintage-blue-tone",
        "name_zh": "复古蓝调",
        "author_zh": "波子Booz",
        "author_en": "Bozi Booz",
        "desc": "明暗反差相对较高，适合顺光拍摄的场景。",
        "tags": ["vintage", "blue", "high-contrast", "front-light"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "jon-simo",
        "lut_slug": "day-for-night",
        "name_zh": "幻化",
        "author_zh": "Jon Simo",
        "author_en": "Jon Simo",
        "desc": "适用于白天模仿夜间拍摄的LUT。",
        "tags": ["day-for-night", "cinematic", "night-sim"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "guo-bin",
        "lut_slug": "fresh-cuisine",
        "name_zh": "清新美食",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "画面整体色调清新自然，赋予了风格化的胶片感。",
        "tags": ["food", "fresh", "natural", "film", "cuisine"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "guo-bin",
        "lut_slug": "camping-vibe",
        "name_zh": "露营氛围",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "色彩偏胶片氛围感，保证画面色彩的同时保留原片的味道。",
        "tags": ["camping", "film", "outdoor", "atmosphere"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "guo-bin",
        "lut_slug": "rice-field-village",
        "name_zh": "稻田乡村",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "绿黄色部分过度协调，人物肤色也保留了胶片色的风格。",
        "tags": ["rural", "green-yellow", "film", "portrait", "village"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "guo-bin",
        "lut_slug": "warm-village",
        "name_zh": "温暖乡村",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "整体色调是复古胶片色，暗部的一些绿色呈现出青绿色。",
        "tags": ["warm", "rural", "film", "cyan-green", "vintage"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "guo-bin",
        "lut_slug": "dusk-atmosphere",
        "name_zh": "黄昏氛围",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "整体色调自然舒适，保留了暗部细节突出傍晚的氛围。",
        "tags": ["dusk", "natural", "shadow-detail", "atmosphere"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "guo-bin",
        "lut_slug": "golden-rice-field",
        "name_zh": "金色稻田",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "绿色以及黄色部分过度的更加协调，保留了胶片色的风格。",
        "tags": ["golden", "rural", "film", "rice-field", "autumn"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "guo-bin",
        "lut_slug": "verdant-scenery",
        "name_zh": "青绿风景",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "整体色系偏胶片氛围感，可以让画面风格化变得强烈。",
        "tags": ["landscape", "green", "film", "verdant"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "hailuoke",
        "lut_slug": "positive-film",
        "name_zh": "正片",
        "author_zh": "海螺壳",
        "author_en": "Hailuoke",
        "desc": "鲜明的红蓝黄色彩直出，基于胶卷正片色彩设计而成。",
        "tags": ["film", "positive-film", "vivid", "red-blue-yellow"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "ejay",
        "lut_slug": "cinema-tone",
        "name_zh": "影院色调",
        "author_zh": "EJAY",
        "author_en": "EJAY",
        "desc": "色调柔和低饱和，蓝色会往青色偏移。",
        "tags": ["cinematic", "low-saturation", "cyan-shift", "soft"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "ejay",
        "lut_slug": "warm-film-tone",
        "name_zh": "暖调胶片",
        "author_zh": "EJAY",
        "author_en": "EJAY",
        "desc": "色调较暖对比强，拥有浓厚胶片味道。",
        "tags": ["film", "warm", "high-contrast"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "xiao-zhai",
        "lut_slug": "candy-color",
        "name_zh": "糖果色",
        "author_zh": "小翟同学",
        "author_en": "Xiao Zhai",
        "desc": "糖果色；低饱和度高明度；青蓝色天空+橙黄色建筑撞色。",
        "tags": [
            "candy",
            "low-saturation",
            "high-brightness",
            "cyan-orange",
            "architecture",
        ],
    },
    {
        "cat": "outdoor",
        "auth_slug": "tu-xiaodai",
        "lut_slug": "blue-ripple",
        "name_zh": "蓝漾",
        "author_zh": "兔小呆",
        "author_en": "Tu Xiaodai",
        "desc": "一款轻日系微冷调的调色LUT，着重进行了肤色的优化，没有很重的风格化影调，泛用性强，在阴天环境下也适用，适合初学者使用。",
        "tags": ["japanese-style", "cool-tone", "skin-tone", "versatile", "beginner"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "qingtian",
        "lut_slug": "sunny-mint",
        "name_zh": "晴天薄荷",
        "author_zh": "晴天",
        "author_en": "Qingtian",
        "desc": "专为人像与绿植设计的薄荷味LUT，灵感源自松下经典色彩，通过微偏青绿的低对比色调、受保护的粉润肤色与低饱和青翠绿植，轻松打造通透干净、充满呼吸感的日系清新影像。建议在柔和光线下配合轻微过曝使用。",
        "tags": ["portrait", "mint", "green", "japanese-style", "fresh"],
    },
    {
        "cat": "outdoor",
        "auth_slug": "zhou",
        "lut_slug": "patina-of-rain",
        "name_zh": "苔痕雨季",
        "author_zh": "舟zhou",
        "author_en": "Zhou",
        "desc": "专为阴雨与多云天气设计的景观LUT，通过重塑绿色光谱，将其转化为柔和、深沉且充满生命力的色调，如同雨后被浸润的青苔，温润而安宁。",
        "tags": ["landscape", "rain", "green", "moss", "moody"],
    },
    # === indoor ===
    {
        "cat": "indoor",
        "auth_slug": "hailuoke",
        "lut_slug": "bw-old-film",
        "name_zh": "黑白旧胶片",
        "author_zh": "海螺壳",
        "author_en": "Hailuoke",
        "desc": "低对比的暗部和亮部，高宽容度的宛如传统黑白电影。",
        "tags": ["bw", "black-and-white", "film", "low-contrast", "high-latitude"],
    },
    {
        "cat": "indoor",
        "auth_slug": "guo-bin",
        "lut_slug": "film-vintage",
        "name_zh": "胶片复古",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "整体色彩饱满，整体呈现暖黄复古的色彩感。",
        "tags": ["film", "vintage", "warm-yellow", "indoor"],
    },
    {
        "cat": "indoor",
        "auth_slug": "guo-bin",
        "lut_slug": "food-film",
        "name_zh": "美食胶片",
        "author_zh": "郭宾",
        "author_en": "Guo Bin",
        "desc": "画面色调清新自然，食物本身色彩赋予了风格化的胶片感。",
        "tags": ["food", "film", "fresh", "natural"],
    },
    {
        "cat": "indoor",
        "auth_slug": "plady",
        "lut_slug": "white-negative",
        "name_zh": "白色负片",
        "author_zh": "Plady",
        "author_en": "Plady",
        "desc": "风格清淡低饱和度的特性，类似留银冲洗的复古胶片感。",
        "tags": ["film", "low-saturation", "bleach-bypass", "retro", "white"],
    },
    {
        "cat": "indoor",
        "auth_slug": "jon-simo",
        "lut_slug": "vintage-vibes",
        "name_zh": "怀旧",
        "author_zh": "Jon Simo",
        "author_en": "Jon Simo",
        "desc": "明显的暖色调，复古氛围感怀旧LUT。",
        "tags": ["vintage", "warm", "nostalgic", "indoor"],
    },
    {
        "cat": "indoor",
        "auth_slug": "hailuoke",
        "lut_slug": "vintage-old-film",
        "name_zh": "复古旧胶片",
        "author_zh": "海螺壳",
        "author_en": "Hailuoke",
        "desc": "基于旧胶片设计的色彩配比。整体偏暖，浓郁的怀旧感。",
        "tags": ["film", "vintage", "warm", "nostalgic"],
    },
    {
        "cat": "indoor",
        "auth_slug": "hailuoke",
        "lut_slug": "magenta-old-film",
        "name_zh": "洋红旧胶片",
        "author_zh": "海螺壳",
        "author_en": "Hailuoke",
        "desc": "整体偏洋红，带来故事叙述的怀旧感。",
        "tags": ["film", "magenta", "nostalgic", "storytelling"],
    },
    {
        "cat": "indoor",
        "auth_slug": "ejay",
        "lut_slug": "film-impression",
        "name_zh": "胶片印象",
        "author_zh": "EJAY",
        "author_en": "EJAY",
        "desc": "经典复古，可以机内模拟颗粒效果。",
        "tags": ["film", "vintage", "grain", "classic"],
    },
    {
        "cat": "indoor",
        "auth_slug": "qingtian",
        "lut_slug": "light-green",
        "name_zh": "轻柔绿意",
        "author_zh": "晴天",
        "author_en": "Qingtian",
        "desc": "以电影感绿色系为核心，在呈现高级绿色质感的同时，精准保护人物肤色的通透感。特别为LUMIX相机优化。建议在充足光线下稍加曝光使用。",
        "tags": ["cinematic", "green", "portrait", "skin-tone", "fresh"],
    },
]

CATEGORY_META = {
    "anniversary": {"name_zh": "25周年专属", "name_en": "25th Anniversary"},
    "portrait": {"name_zh": "人像", "name_en": "Portrait"},
    "outdoor": {"name_zh": "户外", "name_en": "Outdoor"},
    "indoor": {"name_zh": "室内", "name_en": "Indoor"},
}


def parse_cube(path):
    """Parse .cube file to extract metadata."""
    info = {
        "format": "cube",
        "lut_3d_size": None,
        "domain_min": None,
        "domain_max": None,
        "title": None,
        "generator": None,
        "copyright": None,
        "photo_style": None,
        "color_profile": None,
        "comment_lines": [],
    }
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue
            # LUT_3D_SIZE
            m = re.match(r"LUT_3D_SIZE\s+(\d+)", line)
            if m:
                info["lut_3d_size"] = int(m.group(1))
            # DOMAIN_MIN
            m = re.match(r"DOMAIN_MIN\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", line)
            if m:
                info["domain_min"] = [
                    float(m.group(1)),
                    float(m.group(2)),
                    float(m.group(3)),
                ]
            # DOMAIN_MAX
            m = re.match(r"DOMAIN_MAX\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", line)
            if m:
                info["domain_max"] = [
                    float(m.group(1)),
                    float(m.group(2)),
                    float(m.group(3)),
                ]
            # TITLE
            m = re.match(r'TITLE\s+"([^"]*)"', line)
            if m:
                info["title"] = m.group(1)
            # Comments
            if line.startswith("#"):
                info["comment_lines"].append(line[1:].strip())
                # Generator detection
                if "Created by Adobe Lightroom" in line:
                    m2 = re.search(r"Export LUT \(([\d.]+)\)", line)
                    info["generator"] = (
                        f"Adobe Lightroom {m2.group(1)}" if m2 else "Adobe Lightroom"
                    )
                elif "Generated by Picture Instruments" in line:
                    info["generator"] = "Picture Instruments Look Converter"
                elif "LUMIXPHOTOSTYLE" in line:
                    m2 = re.search(r"LUMIXPHOTOSTYLE\s+(\w+)", line)
                    info["photo_style"] = m2.group(1) if m2 else None
                elif "Adobe Photoshop Export" in line:
                    info["generator"] = "Adobe Photoshop"
                elif "Created by Desong" in line or "DESONG" in line.upper():
                    info["generator"] = "hand-authored"
                    if "Created by" in line:
                        info["copyright"] = line[1:].strip()
                elif "Copyright" in line:
                    info["copyright"] = line[1:].strip()
                # Color profile
                m2 = re.search(r"Color profile:\s*(.+)", line)
                if m2:
                    info["color_profile"] = m2.group(1)
                # Preset name
                m2 = re.search(r"Preset:\s*(.+)", line)
                if m2:
                    if not info["title"]:
                        info["title"] = m2.group(1)

        # Detect generators from TITLE
        if not info["generator"]:
            if info.get("title") == "Generated by Resolve":
                info["generator"] = "DaVinci Resolve"
            elif info.get("title") == "Generated by LUMIX Lab":
                info["generator"] = "LUMIX Lab"
            elif info.get("title") and "Generated by" in info["title"]:
                info["generator"] = info["title"].replace("Generated by ", "")
    except Exception as e:
        info["error"] = str(e)
    return info


def parse_vlt(path):
    """Parse .vlt file to extract metadata."""
    info = {
        "format": "vlt",
        "lut_3d_size": None,
        "source": None,
        "generator": "panasonic-vlt",
    }
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        for line in content.split("\n"):
            line = line.strip()
            m = re.match(r"LUT_3D_SIZE\s+(\d+)", line)
            if m:
                info["lut_3d_size"] = int(m.group(1))
            m = re.match(r'#\s*source vlt file\s+"([^"]*)"', line)
            if m:
                info["source"] = m.group(1)
    except Exception as e:
        info["error"] = str(e)
    return info


def hash_file(path):
    """SHA256 of file."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def download_preview(url, dest):
    """Download preview image."""
    if dest.exists():
        return True
    try:
        req = urllib.request.Request(
            url,
            headers={
                **HEADERS,
                "Referer": "http://www.panasonicshuma.cn/RealtimeLUTLibrary/list.aspx",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"    Preview FAIL: {e}")
        return False


def fetch_preview_urls():
    """Fetch all 4 category pages and extract preview image URLs + download IDs."""
    preview_map = {}  # lut_slug -> preview_url
    lcid_map = {"anniversary": "113", "portrait": "32", "outdoor": "33", "indoor": "34"}

    for cat_slug, lcid in lcid_map.items():
        url = f"http://www.panasonicshuma.cn/RealtimeLUTLibrary/list.aspx?lcid={lcid}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"  Failed to fetch {cat_slug}: {e}")
            continue

        # Split by <li data-small=" to get individual LUT blocks
        blocks = re.split(r'<li data-small="([^"]*)"', html)
        # blocks[0] is before first match, then pairs: [1]=preview_url, [2]=block_html, [3]=preview_url, ...
        for i in range(1, len(blocks), 2):
            preview_src = htmlmod.unescape(blocks[i])
            block = blocks[i + 1] if i + 1 < len(blocks) else ""

            # Extract title from <h2>
            title_m = re.search(r"<h2>(.*?)</h2>", block)
            title = htmlmod.unescape(title_m.group(1).strip()) if title_m else ""
            if title.startswith("by "):
                title = title[3:]
            elif title.startswith("by"):
                title = title[2:]
            title = title.strip()

            # Match to catalog entry
            for entry in CATALOG:
                if entry["cat"] != cat_slug:
                    continue
                if entry["name_zh"] in title and entry["author_zh"] in title:
                    full_url = (
                        "http://www.panasonicshuma.cn" + preview_src
                        if preview_src.startswith("/")
                        else preview_src
                    )
                    if entry["lut_slug"] not in preview_map:
                        preview_map[entry["lut_slug"]] = full_url
                    break

        print(
            f"  {cat_slug}: found {len([k for k in preview_map if any(e['cat'] == cat_slug and e['lut_slug'] == k for e in CATALOG)])} preview URLs"
        )

    return preview_map


def main():
    print("=" * 60)
    print("Phase 2: Build luts.json database")
    print("=" * 60)

    # Step 1: Parse all .cube and .vlt files
    print("\n[1/4] Parsing LUT files for internal metadata...")
    results = []

    for entry in CATALOG:
        lut_dir = BASE / entry["cat"] / entry["lut_slug"]
        if not lut_dir.exists():
            print(f"  SKIP: {entry['lut_slug']} (dir not found)")
            continue

        files = []
        total_size = 0

        for f in sorted(lut_dir.iterdir()):
            if f.is_dir():
                continue
            if f.name.startswith("._") or f.name == ".DS_Store":
                continue

            ext = f.suffix.lower()
            if ext == ".md":
                # Read description as fallback
                md_content = f.read_text(encoding="utf-8")
                # Extract description from md
                desc_m = re.search(
                    r"## 简介\n\n(.+?)(?:\n##|\Z)", md_content, re.DOTALL
                )
                if desc_m and not entry.get("desc_from_md"):
                    pass  # Use catalog desc as primary
                continue

            file_size = f.stat().st_size
            total_size += file_size
            file_hash = hash_file(f)

            file_entry = {
                "name": f.name,
                "type": ext.lstrip("."),
                "size": file_size,
                "sha256": file_hash,
            }

            # Parse internal metadata
            if ext == ".cube":
                meta = parse_cube(f)
                file_entry.update(meta)
            elif ext == ".vlt":
                meta = parse_vlt(f)
                file_entry.update(meta)

            files.append(file_entry)

        if not files:
            print(f"  EMPTY: {entry['lut_slug']}")
            continue

        # Merge internal metadata from first LUT file
        primary = files[0]

        lut_entry = {
            "id": entry["lut_slug"],
            "name_zh": entry["name_zh"],
            "author": {
                "name_zh": entry["author_zh"],
                "name_en": entry.get("author_en", ""),
                "slug": entry["auth_slug"],
            },
            "category": entry["cat"],
            "category_zh": CATEGORY_META[entry["cat"]]["name_zh"],
            "description": entry["desc"],
            "tags": entry.get("tags", []),
            "format": primary.get("format", "cube"),
            "lut_3d_size": primary.get("lut_3d_size"),
            "domain_min": primary.get("domain_min"),
            "domain_max": primary.get("domain_max"),
            "photo_style": primary.get("photo_style"),
            "internal": {
                "title": primary.get("title"),
                "generator": primary.get("generator"),
                "copyright": primary.get("copyright"),
                "color_profile": primary.get("color_profile"),
            },
            "total_size": total_size,
            "files": files,
            "preview_image": f"previews/{entry['lut_slug']}.jpg",
        }
        results.append(lut_entry)

    print(
        f"  Parsed {len(results)} LUTs, {sum(len(r['files']) for r in results)} files"
    )

    # Step 2: Fetch preview image URLs from website
    print("\n[2/4] Fetching preview image URLs...")
    preview_map = fetch_preview_urls()
    print(f"  Total preview URLs: {len(preview_map)}")

    # Step 3: Download preview images
    print("\n[3/4] Downloading preview images...")
    downloaded = 0
    for lut in results:
        slug = lut["id"]
        if slug in preview_map:
            url = preview_map[slug]
            dest = PREVIEW_DIR / f"{slug}.jpg"
            if download_preview(url, dest):
                downloaded += 1
                if downloaded % 10 == 0:
                    print(f"  Downloaded {downloaded}...")
            else:
                # Try common extensions
                for ext in [".png", ".jpeg"]:
                    alt_url = url.rsplit(".", 1)[0] + ext
                    dest_alt = PREVIEW_DIR / f"{slug}{ext}"
                    if download_preview(alt_url, dest_alt):
                        lut["preview_image"] = f"previews/{slug}{ext}"
                        downloaded += 1
                        break
        else:
            print(f"  No preview for: {slug}")

    print(f"  Downloaded {downloaded}/{len(results)} previews")

    # Step 4: Build and write luts.json
    print("\n[4/4] Writing luts.json...")

    # Collect unique authors
    authors = {}
    for r in results:
        a = r["author"]
        if a["slug"] not in authors:
            authors[a["slug"]] = {
                "slug": a["slug"],
                "name_zh": a["name_zh"],
                "name_en": a.get("name_en", ""),
                "lut_count": 1,
            }
        else:
            authors[a["slug"]]["lut_count"] += 1

    # Collect unique tags
    all_tags = sorted(set(tag for r in results for tag in r.get("tags", [])))

    # Collect unique generators
    generators = sorted(
        set(
            r["internal"].get("generator")
            for r in results
            if r["internal"].get("generator")
        )
    )

    db = {
        "meta": {
            "updated": "2026-05-17",
            "total_luts": len(results),
            "total_files": sum(len(r["files"]) for r in results),
            "source": "http://www.panasonicshuma.cn/RealtimeLUTLibrary/list.aspx",
        },
        "categories": [
            {
                "id": k,
                "name_zh": v["name_zh"],
                "name_en": v["name_en"],
                "lut_count": sum(1 for r in results if r["category"] == k),
            }
            for k, v in CATEGORY_META.items()
        ],
        "authors": sorted(authors.values(), key=lambda x: x["name_en"] or x["name_zh"]),
        "tags": all_tags,
        "generators": generators,
        "lut_3d_sizes": sorted(
            set(r["lut_3d_size"] for r in results if r["lut_3d_size"])
        ),
        "formats": sorted(set(r["format"] for r in results)),
        "luts": results,
    }

    json_path = BASE / "luts.json"
    json_path.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

    file_size_kb = json_path.stat().st_size / 1024
    print(f"  Written: {json_path} ({file_size_kb:.1f} KB)")
    print(
        f"  {len(results)} LUTs, {len(authors)} authors, {len(all_tags)} tags, {len(generators)} generators"
    )

    print("\n" + "=" * 60)
    print("Phase 2 complete.")
    print(f"luts.json: {json_path}")
    print(f"Previews: {PREVIEW_DIR} ({len(list(PREVIEW_DIR.glob('*')))} files)")


if __name__ == "__main__":
    main()
