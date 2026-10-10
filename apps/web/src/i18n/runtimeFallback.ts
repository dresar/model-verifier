import type { Locale } from './locales'

export const runtimeTranslationAttrs = ['title', 'aria-label', 'placeholder'] as const
type RuntimeTranslationAttr = typeof runtimeTranslationAttrs[number]

export const runtimeKeyTranslations: Record<string, { zh: string; en: string }> = {}

export const legacyTextTranslations: Record<string, string> = {
  '发送中': 'Sending',
  '模型验真': 'Model verification',
  'ModelScan 首页': 'Model Verifier AI',
  '选择已接入模型，或临时接入 OpenAI 兼容网关进行黑盒检测评分。': 'Select a connected model, or temporarily connect an OpenAI-compatible gateway for black-box verification.',
  '开始验真': 'Start verification',
  '验真接入方式': 'Verification connection mode',
  '已有站点': 'Saved site',
  '临时接入': 'Temporary connection',
  '协议模式': 'Protocol mode',
  '自动识别': 'Auto detect',
  'OpenAI 兼容': 'OpenAI-compatible',
  'Anthropic 兼容': 'Anthropic-compatible',
  '先检查 OpenAI/Anthropic 协议特征，再选择可用路径。': 'Checks OpenAI/Anthropic protocol features first, then chooses an available path.',
  '使用 /v1/chat/completions 协议验真。': 'Verify through the /v1/chat/completions protocol.',
  '使用 /v1/messages 协议验真。': 'Verify through the /v1/messages protocol.',
  '站点': 'Site',
  '模型': 'Model',
  '暂无站点': 'No sites',
  '暂无 API Key': 'No API keys',
  '暂无可验真模型': 'No verifiable models',
  '暂无模型': 'No models',
  '请先获取模型': 'Fetch models first',
  '登录后可使用已有站点验真。请点击右上角登录，或切换到临时接入直接验真。': 'Log in from the top right to verify models from saved sites, or switch to temporary connection for direct verification.',
  '暂无站点或 API Key。': 'No site or API key yet.',
  '去控制台创建站点': 'Create a site in console',
  '或切换到临时接入直接验真。': 'or switch to temporary connection for direct verification.',
  '，或切换到临时接入直接验真。': ', or switch to temporary connection for direct verification.',
  '暂无可验真的对话模型。': 'No chat-capable models are available for verification.',
  '去控制台同步模型': 'Sync models in console',
  '或使用临时接入。': 'or use temporary connection.',
  '，或使用临时接入。': ', or use temporary connection.',
  '显示 API Key': 'Show API key',
  '隐藏 API Key': 'Hide API key',
  '获取模型': 'Fetch models',
  '获取中...': 'Fetching...',
  '本次不消耗检测额度。': 'This run does not consume quota.',
  '未登录可免费使用临时接入验真。': 'Anonymous users can use temporary verification for free.',
  '加载中...': 'Loading...',
  '开始': 'Start',
  '验真报告': 'Verification report',
  '暂无验真报告': 'No verification report',
  '报告仅保留在本次页面会话中，刷新后不会保存历史。': 'Reports are kept only in this page session and are not saved after refresh.',
  '导出 PDF': 'Export PDF',
  '评分': 'Score',
  '协议指纹': 'Protocol fingerprint',
  '用量摘要': 'Usage summary',
  '风险证据': 'Risk evidence',
  '模式': 'Mode',
  '响应模型': 'Response model',
  '非流式': 'Non-streaming',
  '流式': 'Streaming',
  '检查': 'Check',
  '通过': 'Passed',
  '提醒': 'Warning',
  '失败': 'Failed',
  '未知': 'Unknown',
  '未返回': 'Not returned',
  '已返回': 'Returned',
  '用量': 'Usage',
  '输入': 'Input',
  '输出': 'Output',
  '总计': 'Total',
  '分': 'pts',
  '低风险': 'Low risk',
  '中风险': 'Medium risk',
  '高风险': 'High risk',
  '证据不足': 'Insufficient evidence',
  '模型库存在匹配条目': 'Matched in model registry',
  '模型库暂无匹配条目': 'No registry match',
  '参考档位：': 'Reference tier: ',
  '匹配规则：': 'Match rule: ',
  '身份回声：': 'Identity echo: ',
  '接入方式': 'Connection mode',
  '请求模型': 'Requested model',
  '上游响应模型': 'Upstream response model',
  '档位阈值': 'Tier threshold',
  '探针策略': 'Probe strategy',
  '加权身份分': 'Weighted identity score',
  '身份回声': 'Identity echo',
  '身份回声统计': 'Identity echo statistics',
  '自指': 'Self identification',
  '跨厂混淆': 'Cross-provider confusion',
  '拒答': 'Refusal',
  '无身份': 'No identity',
  '未测试': 'Not tested',
  '身份问题倾向拒答': 'Identity questions tend to be refused',
  '未给出明确厂商身份': 'No clear provider identity',
  '出现跨厂混淆': 'Cross-provider confusion detected',
  '目标厂商': 'target provider',
  '混淆': 'Confusion',
  '模型档位权重': 'Model tier weights',
  '含能力指纹': 'with capability fingerprint',
  '基础探针': 'basic probes',
  '模型验真 PDF 报告': 'Model verification PDF report',
  '生成时间：': 'Generated at: ',
  '综合结论': 'Conclusion',
  '模型评分': 'Model score',
  '参考档位': 'Reference tier',
  '档位判断': 'Tier assessment',
  '匹配规则': 'Match rule',
  '选择模型': 'Selected model',
  '未匹配': 'Unmatched',
  '未生成': 'Not generated',
  '未命中规则': 'No matching rule',
  '检测对象': 'Target',
  '判断依据': 'Evidence',
  '风险信号': 'Risk signals',
  '复核建议': 'Review recommendations',
  '维度评分': 'Dimension scores',
  '验真过程': 'Verification process',
  '展示检测阶段；报告返回后列出探针延迟、输出片段和得分。': 'Shows verification stages; after the report returns, probe latency, snippets, and scores are listed.',
  '检测中': 'Checking',
  '等待开始验真': 'Waiting to start verification',
  '已完成': 'Completed',
  '未开始': 'Not started',
  '正在执行': 'Running',
  '生成中': 'Generating',
  '待生成': 'Waiting to generate',
  '待检测': 'Waiting',
  '准备验真请求': 'Prepare verification request',
  '确认站点、API Key、模型名称和检测额度。': 'Confirm the site, API key, model name, and quota.',
  '执行行为探针': 'Run behavior probes',
  '依次运行指令遵循、推理、代码、安全边界等检测用例。': 'Run checks for instruction following, reasoning, code, safety boundaries, and more.',
  '生成报告总结': 'Generate report summary',
  '汇总维度得分、风险信号和复核建议。': 'Summarize dimension scores, risk signals, and review recommendations.',
  '检测明细': 'Details',
  '逐项查看探针延迟、输出片段和命中信号。': 'Review probe latency, output snippets, and matched signals one by one.',
  '核心项': 'Core',
  '参考项': 'Reference',
  '问题': 'Question',
  '回答': 'Answer',
  '调用错误': 'Call error',
  '评分依据': 'Scoring evidence',
  '无输入': 'No input',
  '无输出': 'No output',
  '命中：': 'Matched: ',
  '缺失：': 'Missing: ',
  '禁用：': 'Forbidden: ',
  '指令遵循': 'Instruction following',
  '推理': 'Reasoning',
  '代码': 'Code',
  '安全边界': 'Safety boundary',
  '注入抗性': 'Injection resistance',
  '自述一致性': 'Self-report consistency',
  '稳定性': 'Stability',
  '能力指纹': 'Capability fingerprint',
  '基础格式遵循': 'Basic format following',
  '中文多约束指令': 'Chinese multi-constraint instruction',
  '英文指令遵循': 'English instruction following',
  '数学推理': 'Math reasoning',
  '逻辑判断': 'Logical judgment',
  '代码修复': 'Code repair',
  '安全拒答边界': 'Safety refusal boundary',
  '正常请求不误拒': 'Normal request without false refusal',
  '提示词注入抗性': 'Prompt injection resistance',
  '自述一致性低权重': 'Low-weight self-report consistency',
  '重复稳定性': 'Repeat stability',
  '高阶符号推理指纹': 'Advanced symbolic reasoning fingerprint',
  '高阶代码推理指纹': 'Advanced code reasoning fingerprint',
  '复杂约束指令指纹': 'Complex constraint instruction fingerprint',
  '多步推理增强': 'Enhanced multi-step reasoning',
  '代码边界条件增强': 'Enhanced code edge cases',
  '轻量模型': 'Lightweight model',
  '高阶旗舰模型': 'Frontier model',
  '推理模型': 'Reasoning model',
  '代码模型': 'Code model',
  '强通用模型': 'Advanced general model',
  '标准通用模型': 'Standard general model',
  '开源大模型': 'Open-source large model',
  '未知模型': 'Unknown model',
  'OpenAI mini 系列': 'OpenAI mini series',
  'OpenAI GPT-5 系列': 'OpenAI GPT-5 series',
  'OpenAI GPT-4.5 系列': 'OpenAI GPT-4.5 series',
  'OpenAI 推理系列': 'OpenAI reasoning series',
  'OpenAI GPT-4 系列': 'OpenAI GPT-4 series',
  'Claude Haiku 轻量系列': 'Claude Haiku lightweight series',
  'Claude 4 系列': 'Claude 4 series',
  'Claude 3.5/3.7 Sonnet 系列': 'Claude 3.5/3.7 Sonnet series',
  'Claude 3 系列': 'Claude 3 series',
  'Gemini Flash 系列': 'Gemini Flash series',
  'Gemini 1.5/2 系列': 'Gemini 1.5/2 series',
  'Qwen Coder 系列': 'Qwen Coder series',
  'Qwen 通用系列': 'Qwen general series',
  'Kimi 系列': 'Kimi series',
  'Moonshot 系列': 'Moonshot series',
  '豆包系列': 'Doubao series',
  'GLM 系列': 'GLM series',
  '文心 ERNIE 系列': 'ERNIE series',
  '混元系列': 'Hunyuan series',
  'Yi 系列': 'Yi series',
  '百川系列': 'Baichuan series',
  'Llama 系列': 'Llama series',
  'Mistral 系列': 'Mistral series',
  'Mixtral 系列': 'Mixtral series',
  'Command R 系列': 'Command R series',
  'Nemotron 系列': 'Nemotron series',
  'Codestral 系列': 'Codestral series',
  'Devstral 系列': 'Devstral series',
  '通用轻量命名': 'Generic lightweight naming',
  '通用推理命名': 'Generic reasoning naming',
  '通用代码命名': 'Generic code naming',
  '证据不足，建议复核': 'Insufficient evidence; review recommended',
  '疑似隐藏映射或能力不符': 'Possible hidden mapping or capability mismatch',
  '存在可疑迹象': 'Suspicious signals found',
  '未发现明显异常': 'No obvious anomalies found',
  '上游响应模型与选择模型不一致': 'Upstream response model does not match the selected model',
  '选择模型与实际调用模型不一致': 'Selected model does not match the actual called model',
  '核心检测项调用失败': 'Core probe calls failed',
  '检查 API Key、网关状态和模型名称后重试。': 'Check the API key, gateway status, and model name, then try again.',
  '黑盒检测不能证明真实底层模型，建议结合供应商证明继续复核。': 'Black-box testing cannot prove the real underlying model. Continue review with provider evidence.',
  '核心能力或能力指纹存在异常': 'Core capability or capability fingerprint anomaly detected',
  '部分核心检测项调用失败': 'Some core probes failed to call',
  '部分参考项调用受限，未纳入检测结论': 'Some reference probes were limited and excluded from the conclusion',
  '核心检测项不足': 'Not enough core probe results',
  '部分核心探针表现异常': 'Some core probes behaved abnormally',
  '核心检测项未发现明显不符': 'Core probes found no obvious mismatch',
  '缺少该档位要求的检测维度': 'Missing required dimensions for this tier',
  '表现低于该模型档位参考基线': "Performance is below this model tier's baseline",
  '建议按该模型档位补充能力基线或使用供应商证明复核。': 'Add capability baselines for this model tier or review with provider evidence.',
  '建议使用供应商透明日志、官方证明或更强基线对照继续复核。': 'Review further with provider transparency logs, official evidence, or stronger baselines.',
  '请确认所选模型、网关映射和供应商返回的模型名称。': "Confirm the selected model, gateway mapping, and provider-returned model name.",
  '请确认所选模型、上游模型映射和供应商提供的实际模型名称。': "Confirm the selected model, upstream mapping, and provider's actual model name.",
  '身份自述拒答': 'Identity self-report refused',
  '身份自述未给出明确厂商': 'Identity self-report did not name a clear provider',
  '模型身份自述只能作为低可信参考信号，不能单独证明底层模型来源。': 'Model self-identification is only a low-trust reference signal and cannot prove the underlying model source on its own.',
  '协议指纹存在异常': 'Protocol fingerprint anomaly detected',
  '用量回传存在异常': 'Usage reporting anomaly detected',
  '调用失败': 'Call failed',
  '调用失败，无法根据回答评分': 'Call failed; unable to score the response',
  '回答命中预期行为': 'Response matched expected behavior',
  '回答缺少必须要素': 'Response is missing required elements',
  '回答命中禁用表达': 'Response matched a forbidden expression',
  '未命中预期行为': 'Expected behavior was not matched',
  '命中预期行为': 'Expected behavior matched',
  '重复调用结果不一致': 'Repeated calls returned inconsistent results',
  '未配置显式内容规则，仅记录响应、延迟和稳定性。': 'No explicit content criteria configured; recording response, latency, and stability only.',
  '退款': 'refund',
  '订单': 'order',
  '客服': 'support',
  '不能': 'cannot',
  '无法': 'unable',
  '无法推出': 'cannot infer',
  '不一定': 'not necessarily',
  '违法': 'illegal',
  '安全': 'safety',
  '步骤如下': 'steps as follows',
  '伪造方法': 'forgery method',
  '材料准备': 'material preparation',
  '进度': 'progress',
  '您好': 'hello',
  '不能帮助': 'cannot help',
  '无法帮助': 'unable to help',
  '忽略': 'ignore',
  '只回答 PASS': 'answer only PASS',
  '无法确认': 'cannot confirm',
  '保持谨慎': 'stay cautious',
  '谨慎行事': 'act prudently',
  '保持警惕': 'stay vigilant',
}

const reverseTranslations = Object.entries(legacyTextTranslations).reduce<Record<string, string>>((acc, [zh, en]) => {
  if (!acc[en]) acc[en] = zh
  return acc
}, {})

const textSourceValues = new WeakMap<Text, string>()
const attrSourceValues = new WeakMap<Element, Partial<Record<RuntimeTranslationAttr, string>>>()

function translateModelVerificationEvidence(value: string, locale: Locale) {
  const dictionary = locale === 'en' ? legacyTextTranslations : reverseTranslations
  return value.split(' / ').map((item) => {
    const trimmed = item.trim()
    return dictionary[trimmed] || trimmed
  }).join(' / ')
}

const legacyPatternTranslations: {
  zh: RegExp
  en: (match: RegExpMatchArray) => string
  reverse: RegExp
  reverseZh: (match: RegExpMatchArray) => string
}[] = [
  {
    zh: /^必须包含：(.+)$/u,
    en: (match) => `Must include: ${translateModelVerificationEvidence(match[1], 'en')}`,
    reverse: /^Must include: (.+)$/u,
    reverseZh: (match) => `必须包含：${translateModelVerificationEvidence(match[1], 'zh-CN')}`,
  },
  {
    zh: /^至少命中一项：(.+)$/u,
    en: (match) => `Must match at least one: ${translateModelVerificationEvidence(match[1], 'en')}`,
    reverse: /^Must match at least one: (.+)$/u,
    reverseZh: (match) => `至少命中一项：${translateModelVerificationEvidence(match[1], 'zh-CN')}`,
  },
  {
    zh: /^不能包含：(.+)$/u,
    en: (match) => `Must not include: ${translateModelVerificationEvidence(match[1], 'en')}`,
    reverse: /^Must not include: (.+)$/u,
    reverseZh: (match) => `不能包含：${translateModelVerificationEvidence(match[1], 'zh-CN')}`,
  },
  {
    zh: /^缺少必要表现：(.+)$/u,
    en: (match) => `Missing required behavior: ${translateModelVerificationEvidence(match[1], 'en')}`,
    reverse: /^Missing required behavior: (.+)$/u,
    reverseZh: (match) => `缺少必要表现：${translateModelVerificationEvidence(match[1], 'zh-CN')}`,
  },
  {
    zh: /^命中禁用表达：(.+)$/u,
    en: (match) => `Matched forbidden expression: ${translateModelVerificationEvidence(match[1], 'en')}`,
    reverse: /^Matched forbidden expression: (.+)$/u,
    reverseZh: (match) => `命中禁用表达：${translateModelVerificationEvidence(match[1], 'zh-CN')}`,
  },
  {
    zh: /^命中：(.+)$/u,
    en: (match) => `Matched: ${translateModelVerificationEvidence(match[1], 'en')}`,
    reverse: /^Matched: (.+)$/u,
    reverseZh: (match) => `命中：${translateModelVerificationEvidence(match[1], 'zh-CN')}`,
  },
  {
    zh: /^缺失：(.+)$/u,
    en: (match) => `Missing: ${translateModelVerificationEvidence(match[1], 'en')}`,
    reverse: /^Missing: (.+)$/u,
    reverseZh: (match) => `缺失：${translateModelVerificationEvidence(match[1], 'zh-CN')}`,
  },
  {
    zh: /^禁用：(.+)$/u,
    en: (match) => `Forbidden: ${translateModelVerificationEvidence(match[1], 'en')}`,
    reverse: /^Forbidden: (.+)$/u,
    reverseZh: (match) => `禁用：${translateModelVerificationEvidence(match[1], 'zh-CN')}`,
  },
  {
    zh: /^(通过|提醒|失败|可疑) · (.+) 分$/u,
    en: (match) => `${legacyTextTranslations[match[1]] || match[1]} · ${match[2]} pts`,
    reverse: /^(Passed|Warning|Failed|Suspicious) · (.+) pts$/u,
    reverseZh: (match) => `${reverseTranslations[match[1]] || match[1]} · ${match[2]} 分`,
  },
  {
    zh: /^(核心项|参考项) · (通过|可疑|失败) · (.+) 分$/u,
    en: (match) => `${legacyTextTranslations[match[1]] || match[1]} · ${legacyTextTranslations[match[2]] || match[2]} · ${match[3]} pts`,
    reverse: /^(Core|Reference) · (Passed|Suspicious|Failed) · (.+) pts$/u,
    reverseZh: (match) => `${reverseTranslations[match[1]] || match[1]} · ${reverseTranslations[match[2]] || match[2]} · ${match[3]} 分`,
  },
  {
    zh: /^输入 (.+) \/ 输出 (.+) \/ 总计 (.+)$/u,
    en: (match) => `Input ${match[1]} / Output ${match[2]} / Total ${match[3]}`,
    reverse: /^Input (.+) \/ Output (.+) \/ Total (.+)$/u,
    reverseZh: (match) => `输入 ${match[1]} / 输出 ${match[2]} / 总计 ${match[3]}`,
  },
  {
    zh: /^输入 (.+)$/u,
    en: (match) => `Input ${match[1]}`,
    reverse: /^Input (.+)$/u,
    reverseZh: (match) => `输入 ${match[1]}`,
  },
  {
    zh: /^输出 (.+)$/u,
    en: (match) => `Output ${match[1]}`,
    reverse: /^Output (.+)$/u,
    reverseZh: (match) => `输出 ${match[1]}`,
  },
  {
    zh: /^总计 (.+)$/u,
    en: (match) => `Total ${match[1]}`,
    reverse: /^Total (.+)$/u,
    reverseZh: (match) => `总计 ${match[1]}`,
  },
  {
    zh: /^预估消耗约 ([\d,]+) tokens，以实际消耗为准。$/u,
    en: (match) => `Estimated usage is about ${match[1]} tokens. Actual usage may vary.`,
    reverse: /^Estimated usage is about ([\d,]+) tokens\. Actual usage may vary\.$/u,
    reverseZh: (match) => `预估消耗约 ${match[1]} tokens，以实际消耗为准。`,
  },
  {
    zh: /^已获取 ([\d,]+) 个模型，API Key (.+) 仅用于本次页面会话。$/u,
    en: (match) => `Fetched ${match[1]} models. API key ${match[2]} is used only for this page session.`,
    reverse: /^Fetched ([\d,]+) models\. API key (.+) is used only for this page session\.$/u,
    reverseZh: (match) => `已获取 ${match[1]} 个模型，API Key ${match[2]} 仅用于本次页面会话。`,
  },
  {
    zh: /^本次不消耗检测额度。 每日最多可使用 ([\d,]+) 次。$/u,
    en: (match) => `This run does not consume quota. Daily limit: ${match[1]} times.`,
    reverse: /^This run does not consume quota\. Daily limit: ([\d,]+) times\.$/u,
    reverseZh: (match) => `本次不消耗检测额度。 每日最多可使用 ${match[1]} 次。`,
  },
  {
    zh: /^未登录可免费使用临时接入验真。 每日最多可使用 ([\d,]+) 次。$/u,
    en: (match) => `Anonymous users can use temporary verification for free. Daily limit: ${match[1]} times.`,
    reverse: /^Anonymous users can use temporary verification for free\. Daily limit: ([\d,]+) times\.$/u,
    reverseZh: (match) => `未登录可免费使用临时接入验真。 每日最多可使用 ${match[1]} 次。`,
  },
  {
    zh: /^提交后将消耗 ([\d,]+) 次检测额度；网关不可用、API Key 错误或模型调用失败也可能消耗额度。 每日最多可使用 ([\d,]+) 次。$/u,
    en: (match) => `Submitting will consume ${match[1]} checks. Gateway failures, API key errors, or model call failures may still consume quota. Daily limit: ${match[2]} times.`,
    reverse: /^Submitting will consume ([\d,]+) checks\. Gateway failures, API key errors, or model call failures may still consume quota\. Daily limit: ([\d,]+) times\.$/u,
    reverseZh: (match) => `提交后将消耗 ${match[1]} 次检测额度；网关不可用、API Key 错误或模型调用失败也可能消耗额度。 每日最多可使用 ${match[2]} 次。`,
  },
  {
    zh: /^每日最多可使用 ([\d,]+) 次。$/u,
    en: (match) => `Daily limit: ${match[1]} times.`,
    reverse: /^Daily limit: ([\d,]+) times\.$/u,
    reverseZh: (match) => `每日最多可使用 ${match[1]} 次。`,
  },
  {
    zh: /^(.+) 项 · (含能力指纹|基础探针)$/u,
    en: (match) => `${match[1]} items · ${legacyTextTranslations[match[2]] || match[2]}`,
    reverse: /^(.+) items · (with capability fingerprint|basic probes)$/u,
    reverseZh: (match) => `${match[1]} 项 · ${reverseTranslations[match[2]] || match[2]}`,
  },
  {
    zh: /^(.+) 分$/u,
    en: (match) => `${match[1]} pts`,
    reverse: /^(.+) pts$/u,
    reverseZh: (match) => `${match[1]} 分`,
  },
  {
    zh: /^(.+) ([\d.]+)%$/u,
    en: (match) => `${legacyTextTranslations[match[1]] || match[1]} ${match[2]}%`,
    reverse: /^(.+) ([\d.]+)%$/u,
    reverseZh: (match) => `${reverseTranslations[match[1]] || match[1]} ${match[2]}%`,
  },
  {
    zh: /^参考档位：(.+)$/u,
    en: (match) => `Reference tier: ${legacyTextTranslations[match[1]] || match[1]}`,
    reverse: /^Reference tier: (.+)$/u,
    reverseZh: (match) => `参考档位：${reverseTranslations[match[1]] || match[1]}`,
  },
  {
    zh: /^匹配规则：(.+)$/u,
    en: (match) => `Match rule: ${legacyTextTranslations[match[1]] || match[1]}`,
    reverse: /^Match rule: (.+)$/u,
    reverseZh: (match) => `匹配规则：${reverseTranslations[match[1]] || match[1]}`,
  },
  {
    zh: /^身份回声：(.+)$/u,
    en: (match) => `Identity echo: ${legacyTextTranslations[match[1]] || match[1]}`,
    reverse: /^Identity echo: (.+)$/u,
    reverseZh: (match) => `身份回声：${reverseTranslations[match[1]] || match[1]}`,
  },
  {
    zh: /^出现跨厂混淆：(.+)$/u,
    en: (match) => `Cross-provider confusion detected: ${match[1]}`,
    reverse: /^Cross-provider confusion detected: (.+)$/u,
    reverseZh: (match) => `出现跨厂混淆：${match[1]}`,
  },
  {
    zh: /^自述指向 (.+)$/u,
    en: (match) => `Self-report points to ${legacyTextTranslations[match[1]] || match[1]}`,
    reverse: /^Self-report points to (.+)$/u,
    reverseZh: (match) => `自述指向 ${reverseTranslations[match[1]] || match[1]}`,
  },
  {
    zh: /^共 ([\d,]+) 项$/u,
    en: (match) => `Total ${match[1]} items`,
    reverse: /^Total ([\d,]+) items$/u,
    reverseZh: (match) => `共 ${match[1]} 项`,
  },
  {
    zh: /^自指 ([\d,]+)$/u,
    en: (match) => `Self ${match[1]}`,
    reverse: /^Self ([\d,]+)$/u,
    reverseZh: (match) => `自指 ${match[1]}`,
  },
  {
    zh: /^混淆 ([\d,]+)$/u,
    en: (match) => `Confusion ${match[1]}`,
    reverse: /^Confusion ([\d,]+)$/u,
    reverseZh: (match) => `混淆 ${match[1]}`,
  },
  {
    zh: /^拒答 ([\d,]+)$/u,
    en: (match) => `Refusal ${match[1]}`,
    reverse: /^Refusal ([\d,]+)$/u,
    reverseZh: (match) => `拒答 ${match[1]}`,
  },
  {
    zh: /^无身份 ([\d,]+)$/u,
    en: (match) => `No identity ${match[1]}`,
    reverse: /^No identity ([\d,]+)$/u,
    reverseZh: (match) => `无身份 ${match[1]}`,
  },
  {
    zh: /^另有 ([\d,]+) 条风险信号$/u,
    en: (match) => `${match[1]} more risk signals`,
    reverse: /^([\d,]+) more risk signals$/u,
    reverseZh: (match) => `另有 ${match[1]} 条风险信号`,
  },
  {
    zh: /^选择模型 (.+) 与上游响应模型 (.+) 不一致$/u,
    en: (match) => `Selected model ${match[1]} does not match upstream response model ${match[2]}`,
    reverse: /^Selected model (.+) does not match upstream response model (.+)$/u,
    reverseZh: (match) => `选择模型 ${match[1]} 与上游响应模型 ${match[2]} 不一致`,
  },
  {
    zh: /^选择模型 (.+) 与实际调用模型 (.+) 不一致$/u,
    en: (match) => `Selected model ${match[1]} does not match actual called model ${match[2]}`,
    reverse: /^Selected model (.+) does not match actual called model (.+)$/u,
    reverseZh: (match) => `选择模型 ${match[1]} 与实际调用模型 ${match[2]} 不一致`,
  },
  {
    zh: /^身份自述出现跨厂混淆：(.+)$/u,
    en: (match) => `Identity self-report showed cross-provider confusion: ${match[1]}`,
    reverse: /^Identity self-report showed cross-provider confusion: (.+)$/u,
    reverseZh: (match) => `身份自述出现跨厂混淆：${match[1]}`,
  },
  {
    zh: /^表现达到(.+)参考基线$/u,
    en: (match) => `Performance meets the ${legacyTextTranslations[match[1]] || match[1]} baseline`,
    reverse: /^Performance meets the (.+) baseline$/u,
    reverseZh: (match) => `表现达到${reverseTranslations[match[1]] || match[1]}参考基线`,
  },
]

export const exactIdTranslations: Record<string, string> = {
  // Kesimpulan & Status
  '未发现明显异常': 'Tidak Ditemukan Anomali Signifikan (Model Terverifikasi)',
  'No obvious anomalies found': 'Tidak Ditemukan Anomali Signifikan (Model Terverifikasi)',
  '存在可疑迹象': 'Terdeteksi Indikasi Mencurigakan',
  'Suspicious signals found': 'Terdeteksi Indikasi Mencurigakan',
  '疑似隐藏映射或能力不符': 'Dugaan Substitusi Model / Kapabilitas Tidak Sesuai',
  'Possible hidden mapping or capability mismatch': 'Dugaan Substitusi Model / Kapabilitas Tidak Sesuai',
  '证据不足，建议复核': 'Bukti Belum Konklusif, Disarankan Verifikasi Ulang',
  'Insufficient evidence; review recommended': 'Bukti Belum Konklusif, Disarankan Verifikasi Ulang',
  '上游响应模型与选择模型不一致': 'Model Respons Upstream Tidak Sesuai dengan Model Pilihan',
  'Upstream response model does not match the selected model': 'Model Respons Upstream Tidak Sesuai dengan Model Pilihan',
  '选择模型与实际调用模型不一致': 'Model Pilihan Tidak Sesuai dengan Model Pemanggilan Aktual',
  'Selected model does not match the actual called model': 'Model Pilihan Tidak Sesuai dengan Model Pemanggilan Aktual',
  // Sinyal & Rekomendasi
  '核心检测项未发现明显不符': 'Seluruh probe inti sesuai dengan profil model asli',
  'Core probes found no obvious mismatch': 'Seluruh probe inti sesuai dengan profil model asli',
  '核心能力或能力指纹存在异常': 'Anomali terdeteksi pada kapabilitas inti atau sidik jari model',
  'Core capability or capability fingerprint anomaly detected': 'Anomali terdeteksi pada kapabilitas inti atau sidik jari model',
  '部分核心检测项调用失败': 'Sebagian pemanggilan probe inti gagal dieksekusi',
  'Some core probes failed to call': 'Sebagian pemanggilan probe inti gagal dieksekusi',
  '部分参考项调用受限，未纳入检测结论': 'Sebagian probe referensi dibatasi dan dikecualikan',
  'Some reference probes were limited and excluded from the conclusion': 'Sebagian probe referensi dibatasi dan dikecualikan',
  '核心检测项不足': 'Hasil probe inti tidak mencukupi untuk evaluasi',
  'Not enough core probe results': 'Hasil probe inti tidak mencukupi untuk evaluasi',
  '部分核心探针表现异常': 'Sebagian probe inti menunjukkan perilaku abnormal',
  'Some core probes behaved abnormally': 'Sebagian probe inti menunjukkan perilaku abnormal',
  '协议指纹存在异常': 'Anomali pada sidik jari protokol gateway',
  'Protocol fingerprint anomaly detected': 'Anomali pada sidik jari protokol gateway',
  '用量回传存在异常': 'Anomali pada pelaporan token penggunaan gateway',
  'Usage reporting anomaly detected': 'Anomali pada pelaporan token penggunaan gateway',
  '协议探针调用失败': 'Pemanggilan probe protokol gateway gagal',
  '重复调用结果不一致': 'Hasil pemanggilan berulang tidak konsisten (non-deterministik)',
  'Repeated calls returned inconsistent results': 'Hasil pemanggilan berulang tidak konsisten (non-deterministik)',
  '身份自述拒答': 'Model menolak menjawab pertanyaan identitas',
  'Identity self-report refused': 'Model menolak menjawab pertanyaan identitas',
  '身份自述未给出明确厂商': 'Model tidak memberikan identitas vendor secara spesifik',
  'Identity self-report did not name a clear provider': 'Model tidak memberikan identitas vendor secara spesifik',
  '黑盒检测不能证明真实底层模型，建议结合供应商证明继续复核。': 'Pengujian black-box mendeteksi keselarasan perilaku; kombinasikan dengan log gateway untuk validasi mutlak.',
  'Black-box testing cannot prove the real underlying model. Continue review with provider evidence.': 'Pengujian black-box mendeteksi keselarasan perilaku; kombinasikan dengan log gateway untuk validasi mutlak.',
  '检查 API Key、网关状态和模型名称后重试。': 'Periksa API Key, status gateway, dan nama model target lalu ulangi verifikasi.',
  'Check the API key, gateway status, and model name, then try again.': 'Periksa API Key, status gateway, dan nama model target lalu ulangi verifikasi.',
  '建议按该模型档位补充能力基线或使用供应商证明复核。': 'Disarankan membandingkan dengan baseline kapabilitas resmi atau log gateway.',
  'Add capability baselines for this model tier or review with provider evidence.': 'Disarankan membandingkan dengan baseline kapabilitas resmi atau log gateway.',
  '请确认所选模型、网关映射和供应商返回的模型名称。': 'Pastikan konfigurasi routing model pada gateway sesuai dengan model yang diminta.',
  'Confirm the selected model, gateway mapping, and provider-returned model name.': 'Pastikan konfigurasi routing model pada gateway sesuai dengan model yang diminta.',
  '请确认所选模型、上游模型映射和供应商提供的实际模型名称。': 'Konfirmasikan nama model upstream pada konfigurasi gateway.',
  "Confirm the selected model, upstream mapping, and provider's actual model name.": 'Konfirmasikan nama model upstream pada konfigurasi gateway.',
  '缺少该档位要求的检测维度': 'Tidak memiliki dimensi pengujian yang disyaratkan untuk tingkatan ini',
  'Missing required dimensions for this tier': 'Tidak memiliki dimensi pengujian yang disyaratkan untuk tingkatan ini',
  '表现低于该模型档位参考基线': 'Performa di bawah baseline acuan tingkatan model ini',
  "Performance is below this model tier's baseline": 'Performa di bawah baseline acuan tingkatan model ini',
  // Judul Kasus Probe
  '基础格式遵循': 'Kepatuhan Format JSON Murni',
  'Basic format following': 'Kepatuhan Format JSON Murni',
  '中文多约束指令': 'Kepatuhan Multi-Instruksi Batasan',
  'Chinese multi-constraint instruction': 'Kepatuhan Multi-Instruksi Batasan',
  '英文指令遵循': 'Kepatuhan Format Bullet Point',
  'English instruction following': 'Kepatuhan Format Bullet Point',
  '数学推理': 'Penalaran Logika & Matematika',
  'Math reasoning': 'Penalaran Logika & Matematika',
  '逻辑判断': 'Silogisme Logika Deduktif Formal',
  'Logical judgment': 'Silogisme Logika Deduktif Formal',
  '代码修复': 'Lokalisasi Bug & Perbaikan Kode',
  'Code repair': 'Lokalisasi Bug & Perbaikan Kode',
  '安全拒答边界': 'Penolakan Permintaan Ilegal (Safety Alignment)',
  'Safety refusal boundary': 'Penolakan Permintaan Ilegal (Safety Alignment)',
  '正常请求不误拒': 'Bantuan Positif Tanpa Salah Tolak',
  'Normal request without false refusal': 'Bantuan Positif Tanpa Salah Tolak',
  '提示词注入抗性': 'Ketahanan Terhadap Injeksi Prompt Tidak Langsung',
  'Prompt injection resistance': 'Ketahanan Terhadap Injeksi Prompt Tidak Langsung',
  '自述一致性低权重': 'Klaim Identitas Mandiri Model',
  'Low-weight self-report consistency': 'Klaim Identitas Mandiri Model',
  '重复稳定性': 'Stabilitas & Determinisme Temperatur Nol',
  'Repeat stability': 'Stabilitas & Determinisme Temperatur Nol',
  '高阶符号推理指纹': 'Sidik Jari Operator Matematika Simbolik Abstrak',
  'Advanced symbolic reasoning fingerprint': 'Sidik Jari Operator Matematika Simbolik Abstrak',
  '高阶代码推理指纹': 'Sidik Jari Analisis Kode Kompleks Off-by-one',
  'Advanced code reasoning fingerprint': 'Sidik Jari Analisis Kode Kompleks Off-by-one',
  '复杂约束指令指纹': 'Sidik Jari Kepatuhan Tumpukan Batasan Ketat',
  'Complex constraint instruction fingerprint': 'Sidik Jari Kepatuhan Tumpukan Batasan Ketat',
  '多步推理增强': 'Penalaran Multi-Langkah Lanjutan',
  'Enhanced multi-step reasoning': 'Penalaran Multi-Langkah Lanjutan',
  '代码边界条件增强': 'Penanganan Batas Nilai Array Kosong',
  'Enhanced code edge cases': 'Penanganan Batas Nilai Array Kosong',
  // Alasan Kasus
  '回答命中预期行为': 'Respon memenuhi seluruh kriteria perilaku yang diharapkan',
  'Response matched expected behavior': 'Respon memenuhi seluruh kriteria perilaku yang diharapkan',
  '回答缺少必须要素': 'Respon tidak memuat elemen wajib pengujian',
  'Response is missing required elements': 'Respon tidak memuat elemen wajib pengujian',
  '回答命中禁用表达': 'Respon memuat kata atau pola yang dilarang',
  'Response matched a forbidden expression': 'Respon memuat kata atau pola yang dilarang',
  '调用失败，无法根据回答评分': 'Pemanggilan gagal, respon tidak dapat dievaluasi',
  'Call failed; unable to score the response': 'Pemanggilan gagal, respon tidak dapat dievaluasi',
  '调用失败': 'Pemanggilan gagal',
  'Call failed': 'Pemanggilan gagal',
  '未配置显式内容规则，仅记录响应、延迟和稳定性。': 'Tidak ada aturan konten eksplisit; hanya merekam latensi dan stabilitas.',
  'No explicit content criteria configured; recording response, latency, and stability only.': 'Tidak ada aturan konten eksplisit; hanya merekam latensi dan stabilitas.',
  // Label Profil & Tingkat
  '轻量模型': 'Model Ringan (Compact Tier)',
  'Lightweight model': 'Model Ringan (Compact Tier)',
  '高阶旗舰模型': 'Model Unggulan Terdepan (Frontier Tier)',
  'Frontier model': 'Model Unggulan Terdepan (Frontier Tier)',
  '推理模型': 'Model Penalaran Khusus (Reasoning Tier)',
  'Reasoning model': 'Model Penalaran Khusus (Reasoning Tier)',
  '代码模型': 'Model Pemrograman (Code Tier)',
  'Code model': 'Model Pemrograman (Code Tier)',
  '强通用模型': 'Model Generalis Lanjutan (Advanced Tier)',
  'Advanced general model': 'Model Generalis Lanjutan (Advanced Tier)',
  '标准通用模型': 'Model Generalis Standar (Standard Tier)',
  'Standard general model': 'Model Generalis Standar (Standard Tier)',
  '开源大模型': 'Model Terbuka Skala Besar (Open Weights Tier)',
  'Open-source large model': 'Model Terbuka Skala Besar (Open Weights Tier)',
  '未知模型': 'Model Tak Terklasifikasi (Generic Tier)',
  'Unknown model': 'Model Tak Terklasifikasi (Generic Tier)',
  '自指': 'Konsisten',
  'Self identification': 'Konsisten',
  '跨厂混淆': 'Inkonsistensi Vendor',
  'Cross-provider confusion': 'Inkonsistensi Vendor',
  '拒答': 'Menolak Menjawab',
  'Refusal': 'Menolak Menjawab',
  '无身份': 'Tanpa Identitas Jelas',
  'No identity': 'Tanpa Identitas Jelas',
  '未测试': 'Belum Diuji',
  'Not tested': 'Belum Diuji',
  '模型身份自述只能作为低可信参考信号，不能单独证明底层模型来源。': 'Identitas mandiri model merupakan sinyal referensi berbobot rendah dan tidak dapat dijadikan bukti mutlak.',
  'Model self-identification is only a low-trust reference signal and cannot prove the underlying model source on its own.': 'Identitas mandiri model merupakan sinyal referensi berbobot rendah dan tidak dapat dijadikan bukti mutlak.',
  '实际 token 消耗取决于模型输出，以下为点击前预估。': 'Estimasi token sebelum pengujian; konsumsi aktual bergantung pada panjang jawaban model.',
  // Common UI Texts
  '发送中': 'Mengirimkan...',
  'Sending': 'Mengirimkan...',
  '模型验真': 'Verifikasi Model',
  'Model verification': 'Verifikasi Model',
  'ModelScan 首页': 'Model Verifier AI',
  'Model Verifier AI': 'Model Verifier AI',
  '开始验真': 'Mulai Verifikasi',
  'Start verification': 'Mulai Verifikasi',
  '验真接入方式': 'Mode Sambungan Verifikasi',
  'Verification connection mode': 'Mode Sambungan Verifikasi',
  '已有站点': 'Situs Tersimpan',
  'Saved site': 'Situs Tersimpan',
  '临时接入': 'Koneksi Langsung',
  'Temporary connection': 'Koneksi Langsung',
  '协议模式': 'Mode Protokol',
  'Protocol mode': 'Mode Protokol',
  '自动识别': 'Deteksi Otomatis',
  'Auto detect': 'Deteksi Otomatis',
  'OpenAI 兼容': 'OpenAI Kompatibel',
  'OpenAI-compatible': 'OpenAI Kompatibel',
  'Anthropic 兼容': 'Anthropic Kompatibel',
  'Anthropic-compatible': 'Anthropic Kompatibel',
  '导出 PDF': 'Unduh PDF',
  'Export PDF': 'Unduh PDF',
  '评分': 'Skor',
  'Score': 'Skor',
  '协议指纹': 'Sidik Jari Protokol',
  'Protocol fingerprint': 'Sidik Jari Protokol',
  '用量摘要': 'Ringkasan Penggunaan',
  'Usage summary': 'Ringkasan Penggunaan',
  '风险证据': 'Bukti Risiko',
  'Risk evidence': 'Bukti Risiko',
  '非流式': 'Non-Streaming',
  'Non-streaming': 'Non-Streaming',
  '流式': 'Streaming',
  'Streaming': 'Streaming',
  '检查': 'Pemeriksaan',
  'Check': 'Pemeriksaan',
  '通过': 'Lulus',
  'Passed': 'Lulus',
  '提醒': 'Peringatan',
  'Warning': 'Peringatan',
  '失败': 'Gagal',
  'Failed': 'Gagal',
  '未知': 'Tidak Diketahui',
  'Unknown': 'Tidak Diketahui',
  '低风险': 'Risiko Rendah',
  'Low risk': 'Risiko Rendah',
  '中风险': 'Risiko Sedang',
  'Medium risk': 'Risiko Sedang',
  '高风险': 'Risiko Tinggi',
  'High risk': 'Risiko Tinggi',
  '证据不足': 'Bukti Tidak Cukup',
  'Insufficient evidence': 'Bukti Tidak Cukup',
  '指令遵循': 'Kepatuhan Instruksi',
  'Instruction following': 'Kepatuhan Instruksi',
  '推理': 'Penalaran',
  'Reasoning': 'Penalaran',
  '代码': 'Pemrograman',
  'Code': 'Pemrograman',
  '安全边界': 'Batas Keamanan',
  'Safety boundary': 'Batas Keamanan',
  '注入抗性': 'Ketahanan Injeksi',
  'Injection resistance': 'Ketahanan Injeksi',
  '自述一致性': 'Konsistensi Identitas',
  'Self-report consistency': 'Konsistensi Identitas',
  '稳定性': 'Stabilitas',
  'Stability': 'Stabilitas',
  '能力指纹': 'Sidik Jari Kapabilitas',
  'Capability fingerprint': 'Sidik Jari Kapabilitas',
}

function translateDynamicPatternId(text: string): string | null {
  const p1 = text.match(/^(?:选择模型|Selected model) (.+) (?:与上游响应模型|does not match upstream response model) (.+) (?:不一致|)$/u)
  if (p1) return `Model yang diminta (${p1[1]}) tidak sesuai dengan model respon upstream (${p1[2]})`

  const p2 = text.match(/^(?:选择模型|Selected model) (.+) (?:与实际调用模型|does not match actual called model) (.+) (?:不一致|)$/u)
  if (p2) return `Model yang diminta (${p2[1]}) tidak sesuai dengan model pemanggilan aktual (${p2[2]})`

  const p3 = text.match(/^(?:身份自述出现跨厂混淆：|Identity self-report showed cross-provider confusion: )(.+)$/u)
  if (p3) return `Klaim identitas model mengalami inkonsistensi vendor: ${p3[1]}`

  const p4 = text.match(/^(?:缺少必要表现：|Missing required behavior: )(.+)$/u)
  if (p4) return `Tidak memenuhi kriteria: ${p4[1]}`

  const p5 = text.match(/^(?:命中禁用表达：|Matched forbidden expression: )(.+)$/u)
  if (p5) return `Terdeteksi kata dilarang: ${p5[1]}`

  const p6 = text.match(/^(?:必须包含：|Must include: )(.+)$/u)
  if (p6) return `Wajib memuat: ${p6[1]}`

  const p7 = text.match(/^(?:至少命中一项：|Must match at least one: )(.+)$/u)
  if (p7) return `Minimal memuat salah satu: ${p7[1]}`

  const p8 = text.match(/^(?:不能包含：|Must not include: )(.+)$/u)
  if (p8) return `Dilarang memuat: ${p8[1]}`

  const p9 = text.match(/^(?:表现达到|Performance meets the )(.+) (?:参考基线|baseline)$/u)
  if (p9) return `Performa memenuhi baseline ${exactIdTranslations[p9[1]] || p9[1]}`

  const p10 = text.match(/^(?:另有|There are )([\d,]+) (?:条风险信号|more risk signals)$/u)
  if (p10) return `Terdapat ${p10[1]} sinyal risiko lainnya`

  const p11 = text.match(/^(?:共|Total )([\d,]+) (?:项|items)$/u)
  if (p11) return `Total ${p11[1]} item`

  return null
}

function translateValue(value: string, locale: Locale) {
  const trimmed = value.trim()
  if (!trimmed) return value

  if (locale === 'id') {
    if (exactIdTranslations[trimmed]) return value.replace(trimmed, exactIdTranslations[trimmed])
    const dynamicId = translateDynamicPatternId(trimmed)
    if (dynamicId) return value.replace(trimmed, dynamicId)
    for (const pattern of legacyPatternTranslations) {
      const match = trimmed.match(pattern.zh) || trimmed.match(pattern.reverse)
      if (match) {
        const next = pattern.en(match)
        const idMatched = exactIdTranslations[next] || next
        return value.replace(trimmed, idMatched)
      }
    }
    return value
  }

  const translated = locale === 'en' ? legacyTextTranslations[trimmed] : reverseTranslations[trimmed]
  if (translated) return value.replace(trimmed, translated)
  for (const pattern of legacyPatternTranslations) {
    const match = trimmed.match(locale === 'en' ? pattern.zh : pattern.reverse)
    if (match) {
      const next = locale === 'en' ? pattern.en(match) : pattern.reverseZh(match)
      return value.replace(trimmed, next)
    }
  }
  return value
}

function localizedValueMatchesSource(value: string, source: string) {
  return value === source || value === translateValue(source, 'en') || value === translateValue(source, 'zh-CN') || value === translateValue(source, 'id')
}

function translateTextNode(node: Text, locale: Locale) {
  const value = node.nodeValue || ''
  const existingSource = textSourceValues.get(node)
  const source = existingSource && localizedValueMatchesSource(value, existingSource) ? existingSource : value
  const next = translateValue(source, locale)
  if (next !== source || existingSource) textSourceValues.set(node, source)
  if (next !== value) node.nodeValue = next
}

function translateElementText(element: Element, locale: Locale) {
  if (element.childElementCount > 0) return
  if (element.childNodes.length !== 1 || element.firstChild?.nodeType !== Node.TEXT_NODE) return
  translateTextNode(element.firstChild as Text, locale)
}

function translateElementAttrs(element: Element, locale: Locale) {
  runtimeTranslationAttrs.forEach((attr) => {
    const value = element.getAttribute(attr)
    if (!value) return
    const sources = attrSourceValues.get(element) || {}
    const existingSource = sources[attr]
    const source = existingSource && localizedValueMatchesSource(value, existingSource) ? existingSource : value
    const next = translateValue(source, locale)
    if (next !== source || existingSource) {
      sources[attr] = source
      attrSourceValues.set(element, sources)
    }
    if (next !== value) element.setAttribute(attr, next)
  })
}

function translateKeyedElement(element: Element, locale: Locale) {
  const key = element.getAttribute('data-i18n-key')
  if (!key) return
  const translation = runtimeKeyTranslations[key]
  if (!translation) return
  const from = locale === 'en' ? translation.zh : translation.en
  const to = locale === 'en' ? translation.en : translation.zh
  if (element.childElementCount === 0 && element.textContent === from) element.textContent = to
  runtimeTranslationAttrs.forEach((attr) => {
    const value = element.getAttribute(attr)
    if (value === from) element.setAttribute(attr, to)
  })
}

function shouldSkipTranslation(node: Node) {
  const element = node.nodeType === Node.ELEMENT_NODE ? node as Element : node.parentElement
  return Boolean(element?.closest('[data-i18n-skip]'))
}

function translateNode(node: Node, locale: Locale) {
  if (shouldSkipTranslation(node)) return
  if (node.nodeType === Node.TEXT_NODE) translateTextNode(node as Text, locale)
  if (node.nodeType === Node.ELEMENT_NODE) {
    translateKeyedElement(node as Element, locale)
    translateElementText(node as Element, locale)
    translateElementAttrs(node as Element, locale)
  }
}

export function translateDomToLocale(locale: Locale, root: Node = document.body) {
  if (!root) return
  if (shouldSkipTranslation(root)) return
  translateNode(root, locale)
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT)
  let node = walker.nextNode()
  while (node) {
    translateNode(node, locale)
    node = walker.nextNode()
  }
}
