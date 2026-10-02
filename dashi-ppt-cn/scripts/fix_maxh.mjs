#!/usr/bin/env node
/**
 * fix_maxh.mjs — 自动修复 dashi-ppt theme09 的 maxH 校验缺陷
 *
 * 根因：
 *   theme09 的某些版式（典型为 theme09_page075 / theme09_page110）把 maxH
 *   （版式最大高度，数字属性）声明为「必须映射的可见属性」；而其余版式一旦收到
 *   maxH 映射就报 unknown prop。validateGoalSpec 在 render 前会因此硬失败。
 *
 * 修复策略（经验证有效，无需改动 dashi-ppt 技能源码）：
 *   对每个 variant：
 *     - 若该 layout 在 live contract 中支持 maxH：
 *         1) 在 slide.content.presentation 写入数值型 presentation.maxH
 *            （取该版式 defaultProps.maxH，兜底 540）；
 *         2) 把 v.contentMap.maxH 映射到 "presentation.maxH"（数字字段，满足必填+数字校验）。
 *     - 若该 layout 不支持 maxH：剔除 v.contentMap.maxH（避免 unknown prop 报错）。
 *
 * 复用 dashi-ppt 引擎的 getLayoutRecord / unknownPropKeys 读取 live contract，
 * 因此本脚本必须能从 dashi-ppt/project/scripts/skill-workflow-utils.mjs 解析主题资源
 * （之前已验证：该模块基于自身位置解析主题包，不依赖 cwd）。
 *
 * 用法：
 *   node fix_maxh.mjs <goal.json> [out.json]
 *   不传 out.json 时原地写回，并先备份为 <goal>.bak.json。
 */
import { getLayoutRecord, unknownPropKeys } from 'file:///C:/Users/29206/.workbuddy/skills/dashi-ppt/project/scripts/skill-workflow-utils.mjs';
import fs from 'node:fs';

const goalPath = process.argv[2];
const outPath = process.argv[3] || null;
if (!goalPath) {
  console.error('用法: node fix_maxh.mjs <goal.json> [out.json]');
  process.exit(2);
}

const g = JSON.parse(fs.readFileSync(goalPath, 'utf8'));

const cache = new Map();
function layoutSupportsMaxH(layout) {
  if (cache.has(layout)) return cache.get(layout);
  let rec = null;
  try { rec = getLayoutRecord(layout); } catch { rec = null; }
  if (!rec) { cache.set(layout, false); return false; }
  // unknownPropKeys 返回空数组 => maxH 是已知 prop（该版式支持）
  const uk = unknownPropKeys(rec, { maxH: 540 });
  const ok = Array.isArray(uk) && uk.length === 0;
  cache.set(layout, ok);
  return ok;
}
function defaultMaxH(layout) {
  try {
    const rec = getLayoutRecord(layout);
    const dp = rec?.defaultProps || {};
    if (typeof dp.maxH === 'number') return dp.maxH;
  } catch { /* ignore */ }
  return 540; // 兜底值
}

let supported = 0, unsupported = 0, addField = 0, mapNum = 0, removed = 0;
for (const s of g.slides) {
  const pres = s.content?.presentation || {};
  for (const v of s.variants || []) {
    const lay = v.layout;
    if (layoutSupportsMaxH(lay)) {
      supported++;
      if (pres.maxH === undefined) { pres.maxH = defaultMaxH(lay); addField++; }
      v.contentMap = v.contentMap || {};
      if (v.contentMap.maxH !== 'presentation.maxH') { v.contentMap.maxH = 'presentation.maxH'; mapNum++; }
    } else {
      unsupported++;
      if (v.contentMap && 'maxH' in v.contentMap) { delete v.contentMap.maxH; removed++; }
    }
  }
}

const target = outPath || goalPath;
if (!outPath) fs.writeFileSync(goalPath + '.bak.json', fs.readFileSync(goalPath));
fs.writeFileSync(target, JSON.stringify(g, null, 2));

console.log(`[fix_maxh] 支持 maxH 的 variant: ${supported} | 不支持(已剔除 maxH): ${unsupported}`);
console.log(`[fix_maxh] 新增 presentation.maxH: ${addField} | 映射 contentMap.maxH: ${mapNum} | 剔除多余 maxH: ${removed}`);
console.log(`[fix_maxh] 已写入: ${target}`);
