---
name: html-tool-dom-stub-test
description: 对无构建、无依赖的单文件 HTML 工具（在线测评/计算器/数据汇总页等）做真实功能回归测试——用 Node + 最小 DOM 桩把页面里的 <script> 真跑一遍，验证回调绑定、计时、计算、DOM 写入是否正确。触发场景：改完一个自包含 HTML 工具（尤其含计分/计时/解析逻辑）需要验证、用户反馈"页面上看不到某个数据"、需要证明功能没被改坏、手工点页面不方便或不可靠时。触发词：验证 HTML 工具、测试这个网页、页面功能回归、自包含 HTML 自测、DOM 桩测试。
agent_created: true
---

# 单文件 HTML 工具的功能回归测试（Node + 最小 DOM 桩）

## 为什么要这么做

自包含单文件 HTML 工具（一个 `index.html` 里含样式 + 脚本，无 npm、无构建）通常只有两种验证手段：

| 手段 | 能抓住什么 | 抓不住什么 |
|---|---|---|
| `new Function(js)` 语法检查 | 语法错误、括号不匹配 | `$('id')` 返回 null、回调没绑上、计时器没启动、算出来是 NaN |
| 人工点页面 | 表现层问题 | 每次改都要重点、不可重复、容易漏 |

**真实教训**：某测评系统"用时统计"字段只写进了下载用的 JSON，既没显示在页面上、也没进回传短码，语法检查全绿但用户实际拿不到数据。**只有在 Node 里把脚本真跑一遍**才能发现这类"逻辑存在但链路不通"的问题。

核心思路：为 `document` / `window` / `localStorage` 等写一个**最小桩**，用 `new Function` 注入页面脚本，然后**手动触发**注册进来的事件回调，断言 DOM 上的结果。

## 标准流程

1. 从 HTML 里抽出脚本：
   ```js
   const html = fs.readFileSync(path, 'utf8');
   const js = html.match(/<script>([\s\S]*?)<\/script>/)[1];
   ```
   注意：若页面有多个 `<script>`，用 `/g` 全部取出并按顺序执行。

2. 建 DOM 桩（模板见下），执行脚本：
   ```js
   new Function('document','window','localStorage','confirm','alert', js)(
     document, window, localStorage, confirm, alert);
   ```
   只把脚本真正需要的全局量作为形参传入，其余（`Date`、`setInterval`、`Math`、`Array`…）用 Node 原生的，**不要覆盖 `Date`**，否则计时逻辑测不了。

3. 构造输入 → 触发回调 → 断言输出：
   ```js
   $('f-sid').value = '2026010101';
   $('btn-start')._h.click();        // 触发已注册的 click 回调
   await sleep(2300);
   assert($('tm').textContent === '用时 00:02');
   ```

4. 断言分三层：
   - **链路**：元素被创建、回调被触发、视图 `hidden` 状态切换正确
   - **数值**：换算/计分/计时结果精确匹配（如 `1832` 秒 → `30.5` 分钟）
   - **兼容**：旧格式输入仍能解析、边界输入被正确拦截

## DOM 桩模板（可直接复制）

```js
const els = {};
function mkEl(id){
  return {
    id:id||'', textContent:'', value:'', hidden:false, className:'', innerHTML:'',
    style:{}, children:[], checked:false, type:'', name:'', href:'', download:'',
    classList:{ _s:new Set(), add(c){this._s.add(c);}, remove(c){this._s.delete(c);}, contains(c){return this._s.has(c);} },
    addEventListener(t,fn){ (this._h = this._h || {})[t] = fn; },   // 关键：记下回调
    appendChild(c){ this.children.push(c); return c; },
    querySelectorAll(){ return []; },
    setAttribute(){}, removeAttribute(){}, select(){}, setSelectionRange(){}, click(){}
  };
}
const docHandlers = {};
const document = {
  hidden:false,
  getElementById(id){ return els[id] || (els[id] = mkEl(id)); },   // 关键：缓存，保证同一 id 同一对象
  createElement(){ return mkEl(); },
  createTextNode(t){ return { textContent:t }; },                  // 容易漏！
  addEventListener(t,fn){ docHandlers[t] = fn; }                   // 用于 visibilitychange 等
};
const store = {};
const localStorage = {
  getItem(k){ return Object.prototype.hasOwnProperty.call(store,k) ? store[k] : null; },
  setItem(k,v){ store[k] = String(v); },
  removeItem(k){ delete store[k]; }
};
const window = { scrollTo(){} };
const alerts = [];
const confirm = () => true;                    // 需要时改成 false 测"取消"分支
const alert   = m => alerts.push(m);
```

## 必踩的坑（按出现频率）

1. **`createTextNode` 忘记实现** → `TypeError: document.createTextNode is not a function`。几乎每个动态渲染页都会用到。
2. **测试里直接用 `els['xxx']` 取输入元素** → `undefined`。脚本只有真正 `getElementById` 过的 id 才在缓存里；表单元素往往只在事件回调里被访问。**统一用 `$ = id => document.getElementById(id)`**，它按需创建。
3. **`classList` 只写 add/remove** → 页面若调 `contains` 会崩，三个都要给。
4. **覆盖了 `Date`** → 计时/时间戳逻辑全部失真。别传。
5. **`document.hidden` 不可写** → 测不了 `visibilitychange` 暂停逻辑。桩里给普通属性即可。
6. **多个 `<script>` 只取了第一个** → 后半段逻辑没执行，"测试通过"是假象。
7. **`Blob` / `URL.createObjectURL` 未实现** → 若调用点在 `try{}catch(){}` 内会被静默吞掉，不影响测试；若在 try 外会直接抛，需补桩。
8. **异步断言没等待** → 计时类断言必须 `await sleep()`，否则必然失败或假通过。
9. **触发回调时的 `this` 绑定（最隐蔽，实测踩过）** → 页面处理器里若写了 `function(){ state.ans[i] = this.value; }`，它依赖 `this` 指向元素（浏览器中成立）。测试若用 `el._h.input()` 调用，`this` 变成 `_h` 对象，`this.value` 是 `undefined`，数据静默丢失，表现是"进度少了 N 条"或"某字段回传为空"。**必须用 `el._h.input.call(el)`**（或 `el._h.click.call(el)`）显式绑定。用闭包变量赋值（`state.ans[i] = val`）的处理器不受影响——所以症状常表现为"恰好差几个字段"，极易误判为生产 bug。**断言失败先怀疑测试桩的 this**，再怀疑页面代码。
10. **表单校验挡住测试路径** → 想进答题/计算页需先过必填校验时，别在测试里逐个填表单（易漏、耦合 UI）。**改用"断点续答/草稿注入"**：按页面存储键（如 `localStorage['xxx_draft_v2']`）写入一份合法存档 → 清空 `els` 缓存 → 重新执行脚本（脚本初始化时会读到存档并显示"继续"按钮）→ 触发"继续"回调即可直达目标页面。生产代码不变，测试更稳。

## 断言输出风格

用 `OK` / `✗ 预期X，实际Y` 逐条打印，最后一眼能扫完。例：

```
--- 2. 计时走动（等待 2.3s）---
计时显示: 用时 00:02 OK
--- 3. 切走页面自动暂停 ---
暂停值: 用时 00:02 → 1.2s 后: 用时 00:02 OK
--- 5. 提交并生成短码 ---
字段数: 5 OK
第4段=用时秒数: 3 OK
第5段=答案串长度: 55 OK
```

## 何时不该用

- 页面依赖真实网络请求、Canvas 渲染、第三方库（echarts 等）→ 桩成本高，改用 Playwright 真浏览器（成本更高但更真）。
- 只需确认语法 → 用 `new Function(js)` 就够，不必上桩。

## 配套建议

- 把测试脚本放在项目的 `.workbuddy/` 下（如 `test-<功能>.js`），与项目一起留存，改一次跑一次。
- 定长编码（答案串、短码）**必须**用脚本验长度，肉眼核对一定会漏。
- 改动前后端成对文件时，两边的**格式约定要同时改、同时测**，并保留旧格式兼容分支。
