import { useEffect, useRef, useState } from 'react';
import { api, describeError } from '../api';
import { useI18n } from '../i18n';
import type { AISettings, ChatMessage } from '../types';

export function ChatPage() {
  const { t } = useI18n();
  const [settings, setSettings] = useState<AISettings | null>(null);
  const [configOpen, setConfigOpen] = useState(false);
  const [form, setForm] = useState({ enabled: false, base_url: '', model: '', api_key: '' });
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [testMsg, setTestMsg] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [lastTools, setLastTools] = useState<string[]>([]);
  const conversationRef = useRef<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .getAiSettings()
      .then((s) => {
        setSettings(s);
        setForm({ enabled: s.enabled, base_url: s.base_url, model: s.model, api_key: '' });
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const save = async () => {
    setSaving(true);
    setSaveMsg(null);
    try {
      const s = await api.saveAiSettings(form);
      setSettings(s);
      setSaveMsg(s.api_key_configured ? t('已保存（API Key 已配置）') : t('已保存（未配置 API Key）'));
      setForm((f) => ({ ...f, api_key: '' }));
    } catch (e) {
      setSaveMsg(`${t('保存失败：')}${describeError(e)}`);
    } finally {
      setSaving(false);
    }
  };

  const test = async () => {
    setTestMsg(t('测试中…'));
    try {
      const r = await api.testAiConnection({
        base_url: form.base_url || undefined,
        model: form.model || undefined,
        api_key: form.api_key || undefined,
      });
      setTestMsg(r.success ? `${t('连接成功：')}${r.message}` : `${t('连接失败：')}${r.message}`);
    } catch (e) {
      setTestMsg(`${t('测试出错：')}${describeError(e)}`);
    }
  };

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    const history: ChatMessage[] = [...messages, { role: 'user', content: text }];
    setMessages(history);
    setInput('');
    setSending(true);
    setChatError(null);
    setLastTools([]);
    try {
      const r = await api.chat(history, conversationRef.current);
      conversationRef.current = r.conversation_id;
      setMessages((m) => [...m, { role: 'assistant', content: r.reply }]);
      setLastTools(r.tools_used ?? []);
    } catch (e) {
      const msg = describeError(e);
      setChatError(msg);
      setMessages((m) => m.slice(0, -1));
    } finally {
      setSending(false);
    }
  };

  const ready = settings?.enabled && settings?.api_key_configured;

  return (
    <div className="chat-page">
      <header className="page-head page-head--chat">
        <h1>{t('AI 助手')}</h1>
        <p className="page-head__sub">
          {ready
            ? `${t('已连接')} ${settings?.model || t('未指定模型')} (${settings?.base_url})`
            : t('未配置模型。点击右上角“配置”连接 OpenAI 兼容接口。')}
        </p>
        <button
          className={`btn config-toggle${configOpen ? ' config-toggle--active' : ''}`}
          onClick={() => setConfigOpen((v) => !v)}
        >
          {configOpen ? t('收起配置') : t('配置')}
        </button>
      </header>

      {configOpen && (
        <section className="panel config-panel">
          <h2>{t('模型配置（OpenAI 兼容）')}</h2>
          <div className="config-form">
            <label>
              Base URL
              <input
                value={form.base_url}
                placeholder="https://api.openai.com/v1"
                onChange={(e) => setForm((f) => ({ ...f, base_url: e.target.value }))}
              />
            </label>
            <label>
              {t('模型（model）')}
              <input
                value={form.model}
                placeholder="gpt-4o-mini / qwen2.5 / ..."
                onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}
              />
            </label>
            <label>
              API Key
              <input
                type="password"
                value={form.api_key}
                placeholder={settings?.api_key_configured ? t('已配置（留空保持不变）') : t('必填')}
                onChange={(e) => setForm((f) => ({ ...f, api_key: e.target.value }))}
              />
            </label>
            <label className="check-label">
              <input
                type="checkbox"
                checked={form.enabled}
                onChange={(e) => setForm((f) => ({ ...f, enabled: e.target.checked }))}
              />
              {t('启用 AI 对话')}
            </label>
            <div className="config-actions">
              <button className="btn btn--primary" onClick={save} disabled={saving}>
                {saving ? t('保存中…') : t('保存配置')}
              </button>
              <button className="btn" onClick={test}>{t('测试连接')}</button>
            </div>
            {saveMsg && <p className="config-msg">{saveMsg}</p>}
            {testMsg && <p className="config-msg">{testMsg}</p>}
            <p className="muted config-note">
              {t('API Key 仅保存在服务端（src/new/.secrets/），不会发送到浏览器，也不会在配置中回显。')}
            </p>
          </div>
        </section>
      )}

      <section className="chat">
        <div className="chat__messages">
          {messages.length === 0 && (
            <div className="chat__empty">
              <p>{t('向 AI 提问关于您已上传数据的问题，例如：')}</p>
              <ul>
                <li>{t('“总入库量是多少？高值回收率呢？”')}</li>
                <li>{t('“哪个批次的成本/吨最高？”')}</li>
                <li>{t('“Residential Demolition 来源的净价值如何？”')}</li>
                <li>{t('“分月展示处理量与回收价值的变化”')}</li>
              </ul>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`chat__msg chat__msg--${m.role}`}>
              <div className="chat__bubble">{m.content}</div>
              {m.role === 'assistant' && lastTools.length > 0 && i === messages.length - 1 && (
                <div className="chat__tools">{t('调用了工具：')}{lastTools.join(' · ')}</div>
              )}
            </div>
          ))}
          {sending && (
            <div className="chat__msg chat__msg--assistant">
               <div className="chat__bubble chat__bubble--typing">{t('思考中…')}</div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {chatError && <div className="chat__error">{chatError}</div>}

        <div className="chat__input">
          <textarea
            rows={2}
            placeholder={ready ? t('输入问题…（Enter 发送，Shift+Enter 换行）') : t('请先完成模型配置')}
            value={input}
            disabled={!ready}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button className="btn btn--primary" onClick={send} disabled={!ready || sending || !input.trim()}>
            {t('发送')}
          </button>
        </div>
      </section>
    </div>
  );
}